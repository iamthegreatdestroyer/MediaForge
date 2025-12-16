"""Tests for schema validation and serialization."""
import pytest
from uuid import uuid4
from datetime import datetime

from src.models.schemas.media import MediaSchema
from src.models.schemas.tag import TagSchema
from src.models.schemas.collection import CollectionSchema


@pytest.mark.asyncio
class TestMediaSchema:
    """Tests for MediaSchema validation."""

    def test_media_schema_valid(self):
        """Test valid media schema."""
        data = {
            "id": str(uuid4()),
            "file_path": "/videos/movie.mp4",
            "file_hash": "abc123def456",
            "media_type": "video",
            "file_size": 1024000,
            "metadata_extracted": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        schema = MediaSchema(**data)
        
        assert schema.file_path == "/videos/movie.mp4"
        assert schema.media_type == "video"
        assert schema.file_size == 1024000

    def test_media_schema_missing_required(self):
        """Test media schema with missing required fields."""
        data = {
            "file_path": "/videos/movie.mp4",
        }
        
        with pytest.raises(ValueError):
            MediaSchema(**data)

    def test_media_schema_invalid_media_type(self):
        """Test media schema with invalid media type."""
        data = {
            "id": str(uuid4()),
            "file_path": "/videos/movie.mp4",
            "file_hash": "abc123",
            "media_type": "invalid",
            "file_size": 1024000,
        }
        
        with pytest.raises(ValueError):
            MediaSchema(**data)

    def test_media_schema_negative_file_size(self):
        """Test media schema with negative file size."""
        data = {
            "id": str(uuid4()),
            "file_path": "/videos/movie.mp4",
            "file_hash": "abc123",
            "media_type": "video",
            "file_size": -1024,
        }
        
        with pytest.raises(ValueError):
            MediaSchema(**data)


@pytest.mark.asyncio
class TestTagSchema:
    """Tests for TagSchema validation."""

    def test_tag_schema_valid(self):
        """Test valid tag schema."""
        data = {
            "id": str(uuid4()),
            "name": "action",
            "description": "Action movies and content",
            "created_at": datetime.now().isoformat(),
        }
        
        schema = TagSchema(**data)
        
        assert schema.name == "action"
        assert schema.description == "Action movies and content"

    def test_tag_schema_empty_name(self):
        """Test tag schema with empty name."""
        data = {
            "id": str(uuid4()),
            "name": "",
        }
        
        with pytest.raises(ValueError):
            TagSchema(**data)

    def test_tag_schema_name_too_long(self):
        """Test tag schema with name exceeding max length."""
        data = {
            "id": str(uuid4()),
            "name": "a" * 256,
        }
        
        with pytest.raises(ValueError):
            TagSchema(**data)


@pytest.mark.asyncio
class TestCollectionSchema:
    """Tests for CollectionSchema validation."""

    def test_collection_schema_valid(self):
        """Test valid collection schema."""
        data = {
            "id": str(uuid4()),
            "name": "My Collection",
            "description": "A test collection",
            "created_at": datetime.now().isoformat(),
        }
        
        schema = CollectionSchema(**data)
        
        assert schema.name == "My Collection"
        assert schema.description == "A test collection"

    def test_collection_schema_empty_name(self):
        """Test collection schema with empty name."""
        data = {
            "id": str(uuid4()),
            "name": "",
        }
        
        with pytest.raises(ValueError):
            CollectionSchema(**data)

    def test_collection_schema_missing_name(self):
        """Test collection schema missing required name."""
        data = {
            "id": str(uuid4()),
            "description": "No name",
        }
        
        with pytest.raises(ValueError):
            CollectionSchema(**data)


@pytest.mark.asyncio  
class TestSchemaConversions:
    """Tests for schema to model conversions."""

    def test_media_schema_to_dict(self):
        """Test converting media schema to dictionary."""
        data = {
            "id": str(uuid4()),
            "file_path": "/videos/movie.mp4",
            "file_hash": "abc123def456",
            "media_type": "video",
            "file_size": 1024000,
        }
        
        schema = MediaSchema(**data)
        result = schema.model_dump()
        
        assert result["file_path"] == "/videos/movie.mp4"
        assert result["media_type"] == "video"

    def test_tag_schema_to_json(self):
        """Test converting tag schema to JSON."""
        data = {
            "id": str(uuid4()),
            "name": "action",
        }
        
        schema = TagSchema(**data)
        json_str = schema.model_dump_json()
        
        assert "action" in json_str
        assert "name" in json_str

    def test_collection_schema_to_dict(self):
        """Test converting collection schema to dictionary."""
        data = {
            "id": str(uuid4()),
            "name": "My Collection",
        }
        
        schema = CollectionSchema(**data)
        result = schema.model_dump()
        
        assert result["name"] == "My Collection"
