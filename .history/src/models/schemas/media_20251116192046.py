"""Pydantic schemas for MediaItem model."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.models.media import MediaType


class MediaItemBase(BaseModel):
    """Base schema with common MediaItem fields."""

    file_path: str = Field(..., description="Absolute path to the media file")
    file_name: str = Field(..., description="Name of the file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_hash: str = Field(
        ..., min_length=64, max_length=128, description="SHA256 file hash"
    )
    mime_type: str = Field(..., description="MIME type of the file")
    media_type: MediaType = Field(..., description="Classification of media")


class MediaItemCreate(MediaItemBase):
    """Schema for creating a new MediaItem."""

    file_created_at: Optional[datetime] = Field(
        None, description="Filesystem creation timestamp"
    )
    file_modified_at: Optional[datetime] = Field(
        None, description="Filesystem modification timestamp"
    )
    last_scanned_at: Optional[datetime] = Field(
        None, description="Last scan timestamp"
    )
    is_processed: bool = Field(
        default=False, description="Whether item has been processed"
    )
    is_compressed: bool = Field(
        default=False, description="Whether item is compressed"
    )
    compression_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Compression ratio if compressed"
    )


class MediaItemUpdate(BaseModel):
    """Schema for updating an existing MediaItem."""

    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = Field(None, gt=0)
    file_hash: Optional[str] = Field(None, min_length=64, max_length=128)
    mime_type: Optional[str] = None
    media_type: Optional[MediaType] = None
    file_created_at: Optional[datetime] = None
    file_modified_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    is_processed: Optional[bool] = None
    is_compressed: Optional[bool] = None
    compression_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)


class MediaItemRead(MediaItemBase):
    """Schema for reading MediaItem from database."""

    id: UUID
    created_at: datetime
    modified_at: datetime
    file_created_at: Optional[datetime] = None
    file_modified_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    is_processed: bool
    is_compressed: bool
    compression_ratio: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MediaItemReadWithRelations(MediaItemRead):
    """Schema including related metadata, tags, and collections."""

    from src.models.schemas.metadata import MediaMetadataRead
    from src.models.schemas.tag import TagRead
    from src.models.schemas.collection import CollectionRead

    media_metadata: Optional[MediaMetadataRead] = None
    tags: List[TagRead] = Field(default_factory=list)
    collections: List[CollectionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "MediaItemBase",
    "MediaItemCreate",
    "MediaItemUpdate",
    "MediaItemRead",
    "MediaItemReadWithRelations",
]
