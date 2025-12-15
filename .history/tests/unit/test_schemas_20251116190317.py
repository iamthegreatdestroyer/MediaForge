"""Unit tests for Pydantic schemas."""

import pytest
from datetime import datetime
from uuid import uuid4

from src.models.media import MediaType
from src.models.schemas import (
    MediaItemCreate,
    MediaItemRead,
    MediaMetadataCreate,
    MediaMetadataRead,
    TagCreate,
    TagRead,
    CollectionCreate,
    CollectionRead,
)


def test_media_item_create_schema():
    """Test MediaItemCreate schema validation."""
    data = {
        "file_path": "/media/test.mp4",
        "file_name": "test.mp4",
        "file_size": 1024000,
        "file_hash": "a" * 64,
        "mime_type": "video/mp4",
        "media_type": MediaType.video,
    }
    item = MediaItemCreate(**data)
    assert item.file_name == "test.mp4"
    assert item.media_type == MediaType.video
    assert item.is_processed is False


def test_media_item_read_schema():
    """Test MediaItemRead schema."""
    data = {
        "id": uuid4(),
        "file_path": "/media/test.mp4",
        "file_name": "test.mp4",
        "file_size": 1024000,
        "file_hash": "a" * 64,
        "mime_type": "video/mp4",
        "media_type": MediaType.video,
        "created_at": datetime.utcnow(),
        "modified_at": datetime.utcnow(),
        "is_processed": True,
        "is_compressed": False,
    }
    item = MediaItemRead(**data)
    assert item.is_processed is True


def test_metadata_create_schema():
    """Test MediaMetadataCreate schema."""
    data = {
        "media_item_id": uuid4(),
        "duration": 120.5,
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "video_codec": "h264",
    }
    metadata = MediaMetadataCreate(**data)
    assert metadata.duration == 120.5
    assert metadata.width == 1920


def test_metadata_validation():
    """Test MediaMetadata field validation."""
    with pytest.raises(ValueError):
        # Invalid latitude
        MediaMetadataCreate(
            media_item_id=uuid4(), latitude=100.0
        )


def test_tag_create_schema():
    """Test TagCreate schema."""
    data = {
        "name": "Favorites",
        "description": "My favorite media",
        "color": "#FF5733",
    }
    tag = TagCreate(**data)
    assert tag.name == "Favorites"
    assert tag.color == "#FF5733"


def test_tag_color_validation():
    """Test Tag color validation."""
    # Valid colors
    TagCreate(name="Test", color="#FF5733")
    TagCreate(name="Test", color="FF5733")
    
    # Invalid color
    with pytest.raises(ValueError):
        TagCreate(name="Test", color="GGGGGG")


def test_collection_create_schema():
    """Test CollectionCreate schema."""
    data = {
        "name": "My Movies",
        "description": "Collection of my favorite movies",
    }
    collection = CollectionCreate(**data)
    assert collection.name == "My Movies"


def test_schema_from_orm():
    """Test schema creation from ORM model attributes."""
    # Simulate ORM model data
    class MockMediaItem:
        id = uuid4()
        file_path = "/media/test.mp4"
        file_name = "test.mp4"
        file_size = 1024000
        file_hash = "a" * 64
        mime_type = "video/mp4"
        media_type = MediaType.video
        created_at = datetime.utcnow()
        modified_at = datetime.utcnow()
        is_processed = True
        is_compressed = False
        file_created_at = None
        file_modified_at = None
        last_scanned_at = None
        compression_ratio = None

    mock_item = MockMediaItem()
    item = MediaItemRead.model_validate(mock_item)
    assert item.file_name == "test.mp4"
    assert item.is_processed is True
