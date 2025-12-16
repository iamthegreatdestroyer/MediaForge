"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class MediaType(str, Enum):
    """Enumeration of supported media types."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


# ============================================================================
# Media Schemas
# ============================================================================

class MediaMetadataResponse(BaseModel):
    """Media metadata response schema."""
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    bit_rate: Optional[int] = None
    codec: Optional[str] = None
    sample_rate: Optional[int] = None

    class Config:
        from_attributes = True


class MediaResponse(BaseModel):
    """Media response schema."""
    id: str = Field(..., description="Unique media identifier")
    filename: str = Field(..., description="Original filename")
    file_path: str = Field(..., description="Filesystem path")
    media_type: MediaType = Field(..., description="Type of media")
    file_size: int = Field(..., description="File size in bytes")
    hash_value: str = Field(..., description="SHA-256 file hash")
    created_at: datetime = Field(..., description="Creation timestamp")
    modified_at: datetime = Field(..., description="Last modification timestamp")
    metadata: MediaMetadataResponse = Field(default_factory=MediaMetadataResponse)
    tags: List[str] = Field(default_factory=list, description="Associated tags")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "media-123",
                "filename": "vacation.jpg",
                "file_path": "/media/vacation.jpg",
                "media_type": "image",
                "file_size": 2048576,
                "hash_value": "abc123...",
                "created_at": "2024-01-01T12:00:00Z",
                "modified_at": "2024-01-01T12:00:00Z",
                "metadata": {"width": 1920, "height": 1080},
                "tags": ["vacation", "beach"],
            }
        }


class CreateMediaRequest(BaseModel):
    """Create media request schema."""
    file_path: str = Field(..., description="Path to media file")
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Initial tags"
    )

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate file path is not empty."""
        if not v.strip():
            raise ValueError("file_path cannot be empty")
        return v


class UpdateMediaRequest(BaseModel):
    """Update media request schema."""
    filename: Optional[str] = Field(None, description="Update filename")
    tags: Optional[List[str]] = Field(None, description="Replace tags")


# ============================================================================
# Tag Schemas
# ============================================================================

class TagResponse(BaseModel):
    """Tag response schema."""
    id: str = Field(..., description="Unique tag identifier")
    name: str = Field(..., description="Tag name")
    description: Optional[str] = Field(None, description="Tag description")
    media_count: int = Field(default=0, description="Number of tagged media")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateTagRequest(BaseModel):
    """Create tag request schema."""
    name: str = Field(..., description="Tag name", min_length=1, max_length=100)
    description: Optional[str] = Field(
        None, description="Tag description", max_length=500
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tag name."""
        if not v.strip():
            raise ValueError("Tag name cannot be empty")
        return v.lower().strip()


class UpdateTagRequest(BaseModel):
    """Update tag request schema."""
    name: Optional[str] = Field(None, description="New tag name", min_length=1)
    description: Optional[str] = Field(None, description="New description")


# ============================================================================
# Collection Schemas
# ============================================================================

class CollectionResponse(BaseModel):
    """Collection response schema."""
    id: str = Field(..., description="Unique collection identifier")
    name: str = Field(..., description="Collection name")
    description: Optional[str] = Field(None, description="Collection description")
    media_count: int = Field(default=0, description="Number of media in collection")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class CreateCollectionRequest(BaseModel):
    """Create collection request schema."""
    name: str = Field(..., description="Collection name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Collection description")


class UpdateCollectionRequest(BaseModel):
    """Update collection request schema."""
    name: Optional[str] = Field(None, description="New collection name")
    description: Optional[str] = Field(None, description="New description")


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Resource not found",
                "code": "NOT_FOUND",
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }


# ============================================================================
# Pagination Schemas
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")
    search: Optional[str] = Field(None, description="Search query")


class PaginatedResponse(BaseModel, Generic=None):
    """Generic paginated response wrapper."""

    class Config:
        generic_origin = None


# ============================================================================
# Search Schemas
# ============================================================================

class SearchRequest(BaseModel):
    """Search request schema."""
    query: str = Field(..., description="Search query", min_length=1)
    media_type: Optional[MediaType] = Field(None, description="Filter by media type")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    skip: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=20, ge=1, le=100, description="Pagination limit")


class SearchResult(BaseModel):
    """Individual search result."""
    media: MediaResponse = Field(..., description="Matched media")
    score: float = Field(..., ge=0, le=1, description="Search relevance score")


class SearchResponse(BaseModel):
    """Search response schema."""
    results: List[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., ge=0, description="Total number of matches")
    skip: int = Field(..., description="Applied offset")
    limit: int = Field(..., description="Applied limit")
