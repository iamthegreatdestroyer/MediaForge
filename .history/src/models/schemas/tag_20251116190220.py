"""Pydantic schemas for Tag model."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    """Base schema with common Tag fields."""

    name: str = Field(..., min_length=1, max_length=128, description="Tag name")
    description: Optional[str] = Field(None, max_length=512, description="Tag description")
    color: Optional[str] = Field(
        None,
        min_length=6,
        max_length=16,
        pattern=r"^#?[0-9A-Fa-f]{6}$",
        description="Hex color code",
    )


class TagCreate(TagBase):
    """Schema for creating a new Tag."""

    pass


class TagUpdate(BaseModel):
    """Schema for updating an existing Tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=512)
    color: Optional[str] = Field(None, min_length=6, max_length=16, pattern=r"^#?[0-9A-Fa-f]{6}$")


class TagRead(TagBase):
    """Schema for reading Tag from database."""

    id: UUID
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagReadWithMediaCount(TagRead):
    """Schema including count of associated media items."""

    media_count: int = Field(default=0, description="Number of media items with this tag")

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagRead",
    "TagReadWithMediaCount",
]
