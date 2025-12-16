"""Tag repository for data access operations on Tag entities."""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.media import Tag
from src.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    """Repository for Tag entities with specialized queries."""

    def __init__(self, session: AsyncSession):
        """Initialize tag repository.
        
        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session, Tag)

    async def find_by_name(self, name: str) -> Tag | None:
        """Find tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            Tag or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def find_by_prefix(self, prefix: str) -> List[Tag]:
        """Find tags with name starting with prefix.
        
        Args:
            prefix: Name prefix to search for
            
        Returns:
            List of matching tags
        """
        stmt = select(self.model_class).where(
            self.model_class.name.startswith(prefix)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_popular(self, limit: int = 20) -> List[Tag]:
        """Get most popular tags by usage count.
        
        Args:
            limit: Number of tags to return
            
        Returns:
            List of popular tags sorted by usage
        """
        from sqlalchemy import func, desc
        
        stmt = select(self.model_class).join(
            self.model_class.media_items
        ).group_by(self.model_class.id).order_by(
            desc(func.count(self.model_class.id))
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unused(self) -> List[Tag]:
        """Get tags that are not assigned to any media item.
        
        Returns:
            List of unused tags
        """
        stmt = select(self.model_class).where(
            ~self.model_class.media_items.any()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_unused(self) -> int:
        """Delete all unused tags.
        
        Returns:
            Number of deleted tags
        """
        unused = await self.get_unused()
        count = 0
        
        for tag in unused:
            await self.delete(tag.id)
            count += 1
        
        return count
