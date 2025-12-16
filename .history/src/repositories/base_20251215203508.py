"""Base repository pattern for data access layer abstraction."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository for CRUD operations and data access.
    
    Provides a standardized interface for all repository implementations,
    enabling clean separation between business logic and data access layers.
    """

    def __init__(self, session: AsyncSession, model_class: type[T]):
        """Initialize repository with database session and model class.
        
        Args:
            session: SQLAlchemy async session
            model_class: ORM model class for type-specific operations
        """
        self.session = session
        self.model_class = model_class

    async def get_by_id(self, id: str | UUID) -> T | None:
        """Retrieve entity by ID.
        
        Args:
            id: Entity ID (string or UUID)
            
        Returns:
            Entity or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of entities
        """
        stmt = select(self.model_class).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """Create a new entity.
        
        Args:
            entity: Entity instance to create
            
        Returns:
            Created entity with ID assigned
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Update an existing entity.
        
        Args:
            entity: Entity instance with updated values
            
        Returns:
            Updated entity
        """
        merged = await self.session.merge(entity)
        await self.session.flush()
        await self.session.refresh(merged)
        return merged

    async def delete(self, id: str | UUID) -> bool:
        """Delete entity by ID.
        
        Args:
            id: Entity ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False

    async def count(self) -> int:
        """Count total entities.
        
        Returns:
            Total count of entities
        """
        stmt = select(func.count()).select_from(self.model_class)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: str | UUID) -> bool:
        """Check if entity exists by ID.
        
        Args:
            id: Entity ID to check
            
        Returns:
            True if exists, False otherwise
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def commit(self) -> None:
        """Commit current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        await self.session.rollback()
