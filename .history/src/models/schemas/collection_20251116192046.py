"""Pydantic schemas for Collection model."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CollectionBase(BaseModel):
    """Base schema with common Collection fields."""

    name: str = Field(
        ..., min_length=1, max_length=128, description="Collection name"
    )
    description: Optional[str] = Field(
        None, max_length=512, description="Collection description"
    )


class CollectionCreate(CollectionBase):
    """Schema for creating a new Collection."""

    pass


class CollectionUpdate(BaseModel):
    """Schema for updating an existing Collection."""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=512)


class CollectionRead(CollectionBase):
    """Schema for reading Collection from database."""

    id: UUID
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollectionReadWithMediaCount(CollectionRead):
    """Schema including count of media items in collection."""

    media_count: int = Field(
        default=0, description="Number of media items in collection"
    )

    model_config = ConfigDict(from_attributes=True)


class CollectionReadWithMedia(CollectionRead):
    """Schema including all media items in the collection."""

    from src.models.schemas.media import MediaItemRead

    media_items: List[MediaItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "CollectionBase",
    "CollectionCreate",
    "CollectionUpdate",
    "CollectionRead",
    "CollectionReadWithMediaCount",
    "CollectionReadWithMedia",
]
