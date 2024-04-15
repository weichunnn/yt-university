from sqlalchemy import Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    UUID,
    JSON,
)  # Importing for more specific types
from . import AlchemyBase, MetadataMixin
from uuid import uuid4


class Video(AlchemyBase, MetadataMixin):
    __tablename__ = "video"

    id: Mapped[UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(index=True, unique=True, nullable=True)
    title: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)
    duration: Mapped[int] = mapped_column(nullable=True)
    language: Mapped[str] = mapped_column(nullable=True)
    transcription: Mapped[JSON] = mapped_column(type_=JSON, nullable=True)
