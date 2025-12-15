"""Flexible metadata model for media items (audio/video/image/etc.)."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class MediaMetadata(UUIDMixin, TimestampMixin, Base):
    """Rich metadata associated with a single media item."""

    __tablename__ = "media_metadata"

    media_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False, index=True
    )

    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    video_codec: Mapped[str | None] = mapped_column(String(64), nullable=True)
    audio_codec: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bitrate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channels: Mapped[int | None] = mapped_column(Integer, nullable=True)
    artist: Mapped[str | None] = mapped_column(String(256), index=True, nullable=True)
    album: Mapped[str | None] = mapped_column(String(256), index=True, nullable=True)
    title: Mapped[str | None] = mapped_column(String(256), index=True, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    genre: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    camera_make: Mapped[str | None] = mapped_column(String(128), nullable=True)
    camera_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    iso: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aperture: Mapped[float | None] = mapped_column(Float, nullable=True)
    shutter_speed: Mapped[str | None] = mapped_column(String(32), nullable=True)
    focal_length: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    media_item: Mapped["MediaItem"] = relationship(
        "MediaItem", back_populates="metadata", uselist=False
    )

__all__ = ["MediaMetadata"]
