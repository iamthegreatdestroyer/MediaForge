"""Pydantic schemas for API request/response validation and serialization."""

from .collection import (
    CollectionBase,
    CollectionCreate,
    CollectionUpdate,
    CollectionRead,
    CollectionReadWithMediaCount,
    CollectionReadWithMedia,
)
from .media import (
    MediaItemBase,
    MediaItemCreate,
    MediaItemUpdate,
    MediaItemRead,
    MediaItemReadWithRelations,
)
from .metadata import (
    MediaMetadataBase,
    MediaMetadataCreate,
    MediaMetadataUpdate,
    MediaMetadataRead,
)
from .tag import (
    TagBase,
    TagCreate,
    TagUpdate,
    TagRead,
    TagReadWithMediaCount,
)

__all__ = [
    # Collection schemas
    "CollectionBase",
    "CollectionCreate",
    "CollectionUpdate",
    "CollectionRead",
    "CollectionReadWithMediaCount",
    "CollectionReadWithMedia",
    # Media schemas
    "MediaItemBase",
    "MediaItemCreate",
    "MediaItemUpdate",
    "MediaItemRead",
    "MediaItemReadWithRelations",
    # Metadata schemas
    "MediaMetadataBase",
    "MediaMetadataCreate",
    "MediaMetadataUpdate",
    "MediaMetadataRead",
    # Tag schemas
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagRead",
    "TagReadWithMediaCount",
]
