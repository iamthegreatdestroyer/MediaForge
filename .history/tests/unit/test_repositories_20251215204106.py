"""Tests for the Repository pattern implementation."""
import pytest
from uuid import uuid4

from src.models.media import MediaItem, Tag, Collection
from src.repositories.media import MediaRepository
from src.repositories.tag import TagRepository
from src.repositories.collection import CollectionRepository


@pytest.mark.asyncio
class TestMediaRepository:
    """Tests for MediaRepository."""

    async def test_create_media_item(self, db_session, media_factory):
        """Test creating a new media item."""
        repo = MediaRepository(db_session)
        
        media = media_factory()
        created = await repo.create(media)
        
        assert created.id is not None
        assert created.file_path == media.file_path
        assert created.media_type == media.media_type

    async def test_find_by_hash(self, db_session, media_factory):
        """Test finding media by file hash."""
        repo = MediaRepository(db_session)
        
        media = media_factory(file_hash="abc123def456")
        await repo.create(media)
        
        found = await repo.find_by_hash("abc123def456")
        
        assert found is not None
        assert found.file_hash == "abc123def456"

    async def test_find_by_hash_not_found(self, db_session):
        """Test finding media by non-existent hash."""
        repo = MediaRepository(db_session)
        
        found = await repo.find_by_hash("nonexistent")
        
        assert found is None

    async def test_find_by_path(self, db_session, media_factory):
        """Test finding media by path."""
        repo = MediaRepository(db_session)
        
        media1 = media_factory(file_path="/videos/movie.mp4")
        media2 = media_factory(file_path="/videos/series/episode.mp4")
        
        await repo.create(media1)
        await repo.create(media2)
        
        found = await repo.find_by_path("/videos")
        
        assert len(found) >= 2

    async def test_find_by_media_type(self, db_session, media_factory):
        """Test finding media by type."""
        repo = MediaRepository(db_session)
        
        video = media_factory(media_type="video")
        audio = media_factory(media_type="audio")
        
        await repo.create(video)
        await repo.create(audio)
        
        videos = await repo.find_by_media_type("video")
        
        assert len(videos) >= 1
        assert all(v.media_type == "video" for v in videos)

    async def test_find_duplicates(self, db_session, media_factory):
        """Test finding duplicate files."""
        repo = MediaRepository(db_session)
        
        # Create duplicates with same hash
        dup1 = media_factory(file_hash="same_hash")
        dup2 = media_factory(file_hash="same_hash")
        unique = media_factory(file_hash="unique_hash")
        
        await repo.create(dup1)
        await repo.create(dup2)
        await repo.create(unique)
        
        duplicates = await repo.find_duplicates()
        
        assert len(duplicates) >= 1
        # Should find our duplicate pair
        found_hashes = [d[0] for d in duplicates]
        assert "same_hash" in found_hashes

    async def test_find_unscanned(self, db_session, media_factory):
        """Test finding media without metadata extracted."""
        repo = MediaRepository(db_session)
        
        scanned = media_factory(metadata_extracted=True)
        unscanned = media_factory(metadata_extracted=False)
        
        await repo.create(scanned)
        await repo.create(unscanned)
        
        results = await repo.find_unscanned(limit=10)
        
        assert len(results) >= 1
        assert all(not r.metadata_extracted for r in results)

    async def test_get_statistics(self, db_session, media_factory):
        """Test getting media library statistics."""
        repo = MediaRepository(db_session)
        
        await repo.create(media_factory(media_type="video"))
        await repo.create(media_factory(media_type="video"))
        await repo.create(media_factory(media_type="audio"))
        
        stats = await repo.get_statistics()
        
        assert "total" in stats
        assert stats["total"] >= 3


@pytest.mark.asyncio
class TestTagRepository:
    """Tests for TagRepository."""

    async def test_create_tag(self, db_session, tag_factory):
        """Test creating a new tag."""
        repo = TagRepository(db_session)
        
        tag = tag_factory(name="action")
        created = await repo.create(tag)
        
        assert created.id is not None
        assert created.name == "action"

    async def test_find_by_name(self, db_session, tag_factory):
        """Test finding tag by name."""
        repo = TagRepository(db_session)
        
        tag = tag_factory(name="comedy")
        await repo.create(tag)
        
        found = await repo.find_by_name("comedy")
        
        assert found is not None
        assert found.name == "comedy"

    async def test_find_by_prefix(self, db_session, tag_factory):
        """Test finding tags by prefix."""
        repo = TagRepository(db_session)
        
        await repo.create(tag_factory(name="action"))
        await repo.create(tag_factory(name="adventure"))
        await repo.create(tag_factory(name="comedy"))
        
        results = await repo.find_by_prefix("act")
        
        assert len(results) >= 1
        assert all(t.name.startswith("act") for t in results)

    async def test_get_unused_tags(self, db_session, tag_factory):
        """Test finding unused tags."""
        repo = TagRepository(db_session)
        
        unused_tag = tag_factory(name="unused")
        await repo.create(unused_tag)
        
        unused = await repo.get_unused()
        
        assert len(unused) >= 1
        assert any(t.name == "unused" for t in unused)


@pytest.mark.asyncio
class TestCollectionRepository:
    """Tests for CollectionRepository."""

    async def test_create_collection(self, db_session, collection_factory):
        """Test creating a new collection."""
        repo = CollectionRepository(db_session)
        
        collection = collection_factory(name="My Collection")
        created = await repo.create(collection)
        
        assert created.id is not None
        assert created.name == "My Collection"

    async def test_find_by_name(self, db_session, collection_factory):
        """Test finding collection by name."""
        repo = CollectionRepository(db_session)
        
        collection = collection_factory(name="Favorites")
        await repo.create(collection)
        
        found = await repo.find_by_name("Favorites")
        
        assert found is not None
        assert found.name == "Favorites"

    async def test_find_by_prefix(self, db_session, collection_factory):
        """Test finding collections by prefix."""
        repo = CollectionRepository(db_session)
        
        await repo.create(collection_factory(name="Movies"))
        await repo.create(collection_factory(name="Music"))
        await repo.create(collection_factory(name="Photos"))
        
        results = await repo.find_by_prefix("Mo")
        
        assert len(results) >= 1
        assert all(c.name.startswith("Mo") for c in results)

    async def test_get_empty_collections(self, db_session, collection_factory):
        """Test finding empty collections."""
        repo = CollectionRepository(db_session)
        
        empty = collection_factory(name="empty")
        await repo.create(empty)
        
        empty_collections = await repo.get_empty_collections()
        
        assert len(empty_collections) >= 1
        assert any(c.name == "empty" for c in empty_collections)
