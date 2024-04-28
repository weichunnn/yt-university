import time
from typing import NamedTuple
from urllib.parse import parse_qs, urlparse

import yt_university.config as config
from fastapi import Body, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from yt_university.config import MAX_JOB_AGE_SECS
from yt_university.crud.video import get_all_videos, get_video, upsert_video
from yt_university.services.process import process
from yt_university.services.summarize import categorize_text, generate_summary
from yt_university.stub import in_progress

logger = config.get_logger(__name__)

web_app = FastAPI()

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Favorite(BaseModel):
    user_id: str
    video_id: str


class InProgressJob(NamedTuple):
    call_id: str
    start_time: int
    status: str


@web_app.post("/api/process")
async def process_workflow(url: str = Body(..., embed=True)):
    from yt_university.database import get_db_session

    # defensive programming
    parsed = urlparse(url)
    id = parse_qs(parsed.query)["v"][0]

    ## assume only youtube videos
    sanitized_url = "https://www.youtube.com/watch?v=" + id

    now = int(time.time())
    try:
        inprogress_job = in_progress[sanitized_url]
        if (
            isinstance(inprogress_job, InProgressJob)
            and (now - inprogress_job.start_time) < MAX_JOB_AGE_SECS
        ):
            existing_call_id = inprogress_job.call_id
            logger.info(
                f"Found existing, unexpired call ID {existing_call_id} for video {sanitized_url}"
            )
            return {"call_id": existing_call_id}
    except KeyError:
        pass

    async with get_db_session() as session:
        video = await get_video(session, id)

    if video and video.transcription is not None:
        raise HTTPException(status_code=400, detail="Video already processed")
    call = process.spawn(sanitized_url)

    in_progress[sanitized_url] = InProgressJob(
        call_id=call.object_id, start_time=now, status="init"
    )

    logger.info(f"Started new call ID {call.object_id}")
    return {"call_id": call.object_id}


@web_app.post("/api/summarize")
async def invoke_transcription(id: str = Body(..., embed=True)):
    from yt_university.database import get_db_session

    async with get_db_session() as session:
        video = await get_video(session, id)

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not video.transcription:
        raise HTTPException(
            status_code=404, detail="Transcription not available for this video"
        )

    async with get_db_session() as session:
        summary = generate_summary.spawn(video.title, video.transcription).get()
        category = categorize_text.spawn(video.title, summary).get()
        video_data = await upsert_video(
            session, video.id, {"summary": summary, "category": category}
        )

    return {
        id: video_data.id,
        "summary": video_data.summary,
        "category": video_data.category,
    }


@web_app.get("/api/status/{call_id}")
async def poll_status(call_id: str):
    from modal.call_graph import InputInfo, InputStatus
    from modal.functions import FunctionCall

    function_call = FunctionCall.from_id(call_id)
    graph: list[InputInfo] = function_call.get_call_graph()

    try:
        function_call.get(timeout=0.1)
    except TimeoutError:
        pass
    except Exception as exc:
        if exc.args:
            inner_exc = exc.args[0]
            if "HTTPError 403" in inner_exc:
                return dict(error="permission denied on video download")
        return dict(error="unknown job processing error")

    try:
        main_stub = graph[0].children[0]
        map_root = main_stub.children[0]
    except IndexError:
        return dict(stage="init", status="in_progress")

    status = dict(
        stage=map_root.function_name,
        status=InputStatus(map_root.status).name,
    )

    if map_root.function_name == "transcribe":
        leaves = map_root.children
        tasks = len({leaf.task_id for leaf in leaves})
        done_segments = len(
            [leaf for leaf in leaves if leaf.status == InputStatus.SUCCESS]
        )
        total_segments = len(leaves)

        status["total_segments"] = total_segments
        status["tasks"] = tasks
        status["done_segments"] = done_segments
    elif (
        map_root.function_name == "summarize" and map_root.status == InputStatus.SUCCESS
    ) or main_stub.status == InputStatus.SUCCESS:
        status["stage"] = "end"
        status["status"] = "DONE"

    return status


@web_app.get("/api/videos")
async def get_videos_by_category_or_all(
    category: str = Query(None, description="The category of the videos to fetch"),
    page: int = Query(1, description="Page number of the results"),
    page_size: int = Query(10, description="Number of results per page"),
):
    """
    Fetch videos optionally filtered by category with pagination.
    """
    from yt_university.database import get_db_session

    async with get_db_session() as session:
        videos = await get_all_videos(session, category, page, page_size)

    if not videos:
        raise HTTPException(status_code=404, detail="No videos found")

    return videos


@web_app.get("/api/video")
async def get_individual_video(
    id: str = Query(
        ..., description="The ID of the video"
    ),  # Use ellipsis to make it a required field
):
    """
    Fetch a video by its ID.
    """
    from yt_university.database import get_db_session

    async with get_db_session() as session:
        video = await get_video(session, id)

    # Check if the video was found
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video


@web_app.get("/api/categories")
async def get_video_categories():
    from yt_university.services.summarize import CATEGORIES

    categories = CATEGORIES

    if not categories:
        raise HTTPException(status_code=404, detail="No categories found")

    return categories


@web_app.post("/api/favorites")
async def add_to_favorites(favorite: Favorite):
    from yt_university.crud.favorite import add_favorite
    from yt_university.database import get_db_session

    print(favorite)
    try:
        async with get_db_session() as session:
            favorite_data = await add_favorite(
                session, favorite.user_id, favorite.video_id
            )
            return favorite_data
    except HTTPException as e:
        raise e


@web_app.delete("/api/favorites")
async def delete_favorite(favorite: Favorite):
    from yt_university.crud.favorite import remove_favorite
    from yt_university.database import get_db_session

    try:
        async with get_db_session() as session:
            await remove_favorite(session, favorite.user_id, favorite.video_id)
            return {"status": "success", "message": "Favorite has been removed"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@web_app.get("/api/favorites/{user_id}")
async def list_favorites(user_id: str):
    from yt_university.crud.favorite import get_user_favorites
    from yt_university.database import get_db_session

    try:
        async with get_db_session() as session:
            favorites = await get_user_favorites(session, user_id)
            return favorites
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
