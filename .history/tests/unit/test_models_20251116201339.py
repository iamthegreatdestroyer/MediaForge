"""Unit tests for ORM models (schema, relationships, CRUD)."""

import pytest
from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError

from src.core.database import Database
from src.models import (
    MediaItem,
    MediaMetadata,
    Tag,
    Collection,
    MediaType,
)


@pytest.fixture(scope="function")
async def db():  # returns Database via async generator
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_tables()
    try:
        yield database
    finally:
        await database.drop_tables()


@pytest.mark.asyncio
async def test_media_item_creation(db: Database):
    async with db.session() as session:
        item = MediaItem(
            file_path="/media/test.mp4",
            file_name="test.mp4",
            file_size=1234,
            file_hash="hash123",
            mime_type="video/mp4",
            media_type=MediaType.video,
        )
        session.add(item)

    async with db.session() as session:
        result = await session.execute(
            select(MediaItem).where(MediaItem.file_hash == "hash123")
        )
        loaded = result.scalar_one()
        assert loaded.file_name == "test.mp4"
        assert loaded.media_type == MediaType.video


@pytest.mark.asyncio
async def test_unique_constraints(db: Database):
    async with db.session() as session:
        first = MediaItem(
            file_path="/media/unique.mp4",
            file_name="unique.mp4",
            file_size=1,
            file_hash="uniquehash",
            mime_type="video/mp4",
            media_type=MediaType.video,
        )
        session.add(first)

    with pytest.raises(IntegrityError):
        async with db.session() as session:
            dup = MediaItem(
                file_path="/media/unique.mp4",
                file_name="unique2.mp4",
                file_size=2,
                file_hash="uniquehash2",
                mime_type="video/mp4",
                media_type=MediaType.video,
            )
            session.add(dup)


@pytest.mark.asyncio
async def test_relationships(db: Database):
    async with db.session() as session:
        item = MediaItem(
            file_path="/media/meta.mp4",
            file_name="meta.mp4",
            file_size=999,
            file_hash="metahash",
            mime_type="video/mp4",
            media_type=MediaType.video,
        )
        meta = MediaMetadata(
            media_item=item,
            duration=10.5,
            width=1920,
            height=1080,
        )
        tag = Tag(name="Sample")
        collection = Collection(name="Set A")
        item.tags.append(tag)
        item.collections.append(collection)
        session.add_all([item, meta, tag, collection])

    async with db.session() as session:
        result = await session.execute(
            select(MediaItem).where(MediaItem.file_hash == "metahash")
        )
        loaded = result.scalar_one()
        assert loaded.media_metadata is not None
        assert loaded.media_metadata.duration == 10.5
        assert loaded.tags[0].name == "Sample"
        assert loaded.collections[0].name == "Set A"


@pytest.mark.asyncio
async def test_indexes_exist(db):
    async with db.engine.begin() as conn:  # type: ignore[attr-defined]
        def _get_indexes(sync_conn):
            return inspect(sync_conn).get_indexes("media_items")

        indexes = await conn.run_sync(_get_indexes)
    names = {idx["name"] for idx in indexes}
    assert "ix_media_items_file_path" in names
    assert "ix_media_items_file_hash" in names
    assert "ix_media_items_media_type_created_at" in names
