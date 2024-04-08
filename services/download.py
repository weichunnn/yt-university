import logging

from modal import Image, Volume, method, stub

from yt_university.config import DATA_DIR
from yt_university.stub import stub

downloader_image = (
    Image.debian_slim(python_version="3.11").apt_install("ffmpeg").pip_install("yt-dlp")
)

volume = Volume.from_name("yt-university-cache", create_if_missing=True)

logger = logging.getLogger(__name__)


@stub.cls(
    container_idle_timeout=60,
    image=downloader_image,
    timeout=600,
    volumes={DATA_DIR: volume},
)
class Downloader:
    @method()
    def run(self, url, output_dir):
        video_path = self.get_youtube(output_dir, url)
        wav_path = self.convert_to_wav(video_path)
        return wav_path

    def get_youtube(self, output_dir, video_url):
        """
        Downloads the audio from a YouTube video and saves metadata to a .info.json file.
        """
        import yt_dlp

        ydl_opts = {
            "format": "bestaudio[ext=m4a]",
            "writethumbnail": True,
            "outtmpl": f"{DATA_DIR}{output_dir}%(id)s.%(ext)s",
        }

        meta_dict = {}
        required_keys_list = ["id", "title", "description", "webpage_url"]
        optional_keys_list = ["duration", "thumbnail", "tags", "language"]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            meta_dict = {key: info.get(key, "") for key in required_keys_list}
            for optional_key in optional_keys_list:
                if optional_key in info:
                    meta_dict.update({optional_key: info.get(optional_key)})
            logger.info(meta_dict)
            ydl.process_info(info)

        video_path = f"{DATA_DIR}{output_dir}{info['id']}.{info['ext']}"
        logger.info(f"Successfully downloaded {video_url} to {video_path}")
        return video_path

    def convert_to_wav(self, video_file_path, offset=0):
        """
        Converts an m4a audio file to WAV format using ffmpeg.
        """
        import os

        if not os.path.exists(video_file_path):
            raise FileNotFoundError("m4a file not found.")

        out_path = video_file_path.replace("m4a", "wav")
        if os.path.exists(out_path):
            logger.info(f"WAV file already exists: {out_path}")
            return out_path

        offset_args = f"-ss {offset}" if offset > 0 else ""
        conversion_command = f'ffmpeg {offset_args} -i "{video_file_path}" -ar 16000 -ac 1 -c:a pcm_s16le "{out_path}"'
        if os.system(conversion_command) != 0:
            raise RuntimeError("Error converting file to WAV.")

        logger.info(f"Conversion to WAV ready: {out_path}")
        volume.commit()
        return out_path
