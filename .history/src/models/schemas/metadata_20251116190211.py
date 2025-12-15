"""Pydantic schemas for MediaMetadata model."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MediaMetadataBase(BaseModel):
    """Base schema with common MediaMetadata fields."""

    # Video fields
    duration: Optional[float] = Field(None, ge=0.0, description="Duration in seconds")
    width: Optional[int] = Field(None, gt=0, description="Video width in pixels")
    height: Optional[int] = Field(None, gt=0, description="Video height in pixels")
    fps: Optional[float] = Field(None, gt=0.0, description="Frames per second")
    video_codec: Optional[str] = Field(None, max_length=64)
    audio_codec: Optional[str] = Field(None, max_length=64)
    bitrate: Optional[int] = Field(None, gt=0, description="Bitrate in bps")

    # Audio fields
    sample_rate: Optional[int] = Field(None, gt=0, description="Sample rate in Hz")
    channels: Optional[int] = Field(
        None, ge=1, le=32, description="Number of audio channels"
    )
    artist: Optional[str] = Field(None, max_length=256)
    album: Optional[str] = Field(None, max_length=256)
    title: Optional[str] = Field(None, max_length=256)
    year: Optional[int] = Field(None, ge=1800, le=2100)
    genre: Optional[str] = Field(None, max_length=128)

    # Image fields
    camera_make: Optional[str] = Field(None, max_length=128)
    camera_model: Optional[str] = Field(None, max_length=128)
    iso: Optional[int] = Field(None, gt=0)
    aperture: Optional[float] = Field(None, gt=0.0)
    shutter_speed: Optional[str] = Field(None, max_length=32)
    focal_length: Optional[float] = Field(None, gt=0.0, description="Focal length in mm")

    # Geolocation
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_name: Optional[str] = Field(None, max_length=256)

    # Extensible metadata
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class MediaMetadataCreate(MediaMetadataBase):
    """Schema for creating MediaMetadata."""

    media_item_id: UUID


class MediaMetadataUpdate(BaseModel):
    """Schema for updating MediaMetadata."""

    duration: Optional[float] = Field(None, ge=0.0)
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    fps: Optional[float] = Field(None, gt=0.0)
    video_codec: Optional[str] = Field(None, max_length=64)
    audio_codec: Optional[str] = Field(None, max_length=64)
    bitrate: Optional[int] = Field(None, gt=0)
    sample_rate: Optional[int] = Field(None, gt=0)
    channels: Optional[int] = Field(None, ge=1, le=32)
    artist: Optional[str] = Field(None, max_length=256)
    album: Optional[str] = Field(None, max_length=256)
    title: Optional[str] = Field(None, max_length=256)
    year: Optional[int] = Field(None, ge=1800, le=2100)
    genre: Optional[str] = Field(None, max_length=128)
    camera_make: Optional[str] = Field(None, max_length=128)
    camera_model: Optional[str] = Field(None, max_length=128)
    iso: Optional[int] = Field(None, gt=0)
    aperture: Optional[float] = Field(None, gt=0.0)
    shutter_speed: Optional[str] = Field(None, max_length=32)
    focal_length: Optional[float] = Field(None, gt=0.0)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_name: Optional[str] = Field(None, max_length=256)
    extra_metadata: Optional[Dict[str, Any]] = None


class MediaMetadataRead(MediaMetadataBase):
    """Schema for reading MediaMetadata from database."""

    id: UUID
    media_item_id: UUID
    created_at: datetime
    modified_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "MediaMetadataBase",
    "MediaMetadataCreate",
    "MediaMetadataUpdate",
    "MediaMetadataRead",
]
