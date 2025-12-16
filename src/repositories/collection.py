"""Collection repository for data access operations on Collection entities."""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.media import Collection
from src.repositories.base import BaseRepository


class CollectionRepository(BaseRepository[Collection]):
    """Repository for Collection entities with specialized queries."""

    def __init__(self, session: AsyncSession):
        """Initialize collection repository.
        
        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Collection)

    async def find_by_name(self, name: str) -> Collection | None:
        """Find collection by name.
        
        Args:
            name: Collection name
            
        Returns:
            Collection or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_prefix(self, prefix: str) -> List[Collection]:
        """Find collections with name starting with prefix.
        
        Args:
            prefix: Name prefix to search for
            
        Returns:
            List of matching collections
        """
        stmt = select(self.model_class).where(
            self.model_class.name.startswith(prefix)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_media_count(self) -> List[tuple[Collection, int]]:
        """Get all collections with their media item counts.
        
        Returns:
            List of tuples (Collection, media_count)
        """
        from sqlalchemy import func
        
        stmt = select(
            self.model_class,
            func.count(self.model_class.media_items).label("count")
        ).group_by(self.model_class.id)
        
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_empty_collections(self) -> List[Collection]:
        """Get collections with no media items.
        
        Returns:
            List of empty collections
        """
        stmt = select(self.model_class).where(
            ~self.model_class.media_items.any()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_empty(self) -> int:
        """Delete all empty collections.
        
        Returns:
            Number of deleted collections
        """
        empty = await self.get_empty_collections()
        count = 0
        
        for collection in empty:
            await self.delete(collection.id)
            count += 1
        
        return count
