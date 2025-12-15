"""Media-related ORM models: MediaItem, Tag, Collection and association tables.

Defines core entities and many-to-many association tables used by MediaForge.
"""

from __future__ import annotations

from datetime import datetime, UTC
from enum import Enum
from typing import List, TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Boolean,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:  # pragma: no cover
    from .metadata import MediaMetadata


class MediaType(str, Enum):
    """Enumeration of supported media types."""

    video = "video"
    audio = "audio"
    image = "image"
    document = "document"
    other = "other"


media_tags = Table(
    "media_tags",
    Base.metadata,
    Column(
        "media_item_id",
        ForeignKey("media_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
)

collection_items = Table(
    "collection_items",
    Base.metadata,
    Column(
        "collection_id",
        ForeignKey("collections.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "media_item_id",
        ForeignKey("media_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("position", Integer, nullable=True),
    Column("added_at", DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False),
)


class MediaItem(UUIDMixin, TimestampMixin, Base):
    """Represents a single media asset stored in the library."""

    __tablename__ = "media_items"

    file_path: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    file_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    mime_type: Mapped[str] = mapped_column(
        String(128), index=True, nullable=False
    )
    media_type: Mapped[MediaType] = mapped_column(
        SAEnum(MediaType), index=True, nullable=False
    )
    file_created_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    file_modified_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    last_scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    is_processed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    is_compressed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    compression_ratio: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    # Relationship renamed internally to avoid clashing with Base.metadata
    media_metadata: Mapped["MediaMetadata | None"] = relationship(
        "MediaMetadata",
        back_populates="media_item",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary=media_tags,
        back_populates="media_items",
        lazy="selectin",
    )
    collections: Mapped[List["Collection"]] = relationship(
        "Collection",
        secondary=collection_items,
        back_populates="media_items",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_media_items_media_type_created_at",
            "media_type",
            "created_at",
        ),
    )


class Tag(UUIDMixin, TimestampMixin, Base):
    """Categorization tag applied to media items."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)

    media_items: Mapped[List[MediaItem]] = relationship(
        "MediaItem", secondary=media_tags, back_populates="tags"
    )


class Collection(UUIDMixin, TimestampMixin, Base):
    """Logical grouping of media items (albums, playlists, sets)."""

    __tablename__ = "collections"

    name: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    media_items: Mapped[List[MediaItem]] = relationship(
        "MediaItem", secondary=collection_items, back_populates="collections"
    )


__all__ = [
    "MediaItem",
    "Tag",
    "Collection",
    "MediaType",
    "media_tags",
    "collection_items",
]
