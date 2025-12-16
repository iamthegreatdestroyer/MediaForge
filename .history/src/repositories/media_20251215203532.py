"""Media repository for data access operations on MediaItem entities."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.media import MediaItem
from src.repositories.base import BaseRepository


class MediaRepository(BaseRepository[MediaItem]):
    """Repository for MediaItem entities with specialized queries."""

    def __init__(self, session: AsyncSession):
        """Initialize media repository.
        
        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, MediaItem)

    async def find_by_hash(self, file_hash: str) -> MediaItem | None:
        """Find media item by file hash.
        
        Args:
            file_hash: SHA-256 file hash
            
        Returns:
            MediaItem or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.file_hash == file_hash)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_path(self, file_path: str) -> List[MediaItem]:
        """Find media items by file path (supports partial matching).
        
        Args:
            file_path: File path to search for
            
        Returns:
            List of matching media items
        """
        stmt = select(self.model_class).where(
            self.model_class.file_path.contains(file_path)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_media_type(self, media_type: str) -> List[MediaItem]:
        """Find media items by type (video, audio, image, etc).
        
        Args:
            media_type: Type of media
            
        Returns:
            List of media items of specified type
        """
        stmt = select(self.model_class).where(
            self.model_class.media_type == media_type
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_duplicates(self) -> List[tuple[str, List[MediaItem]]]:
        """Find duplicate files based on file hash.
        
        Returns:
            List of tuples containing (file_hash, [MediaItems with hash])
        """
        stmt = select(self.model_class).order_by(self.model_class.file_hash)
        result = await self.session.execute(stmt)
        all_items = result.scalars().all()
        
        duplicates = []
        hash_map = {}
        
        for item in all_items:
            if item.file_hash not in hash_map:
                hash_map[item.file_hash] = []
            hash_map[item.file_hash].append(item)
        
        for file_hash, items in hash_map.items():
            if len(items) > 1:
                duplicates.append((file_hash, items))
        
        return duplicates

    async def find_by_collection_id(self, collection_id: UUID) -> List[MediaItem]:
        """Find all media items in a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            List of media items in collection
        """
        stmt = select(self.model_class).where(
            self.model_class.collections.any(id=collection_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_tag_id(self, tag_id: UUID) -> List[MediaItem]:
        """Find all media items with a specific tag.
        
        Args:
            tag_id: ID of the tag
            
        Returns:
            List of media items with tag
        """
        stmt = select(self.model_class).where(
            self.model_class.tags.any(id=tag_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_recent(self, limit: int = 50) -> List[MediaItem]:
        """Find recently added media items.
        
        Args:
            limit: Number of items to return
            
        Returns:
            List of recent media items
        """
        stmt = select(self.model_class).order_by(
            self.model_class.created_at.desc()
        ).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_unscanned(self, limit: int = 100) -> List[MediaItem]:
        """Find media items without metadata extracted yet.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of unscanned media items
        """
        stmt = select(self.model_class).where(
            self.model_class.metadata_extracted == False
        ).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_statistics(self) -> dict:
        """Get media library statistics.
        
        Returns:
            Dictionary with count by media type and total
        """
        from sqlalchemy import func
        
        stmt = select(
            self.model_class.media_type,
            func.count(self.model_class.id).label("count")
        ).group_by(self.model_class.media_type)
        
        result = await self.session.execute(stmt)
        stats = {row[0]: row[1] for row in result.all()}
        stats["total"] = sum(stats.values())
        
        return stats
