"""Async database engine and session management for MediaForge."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from src.models import Base
from src.core.config import settings  # type: ignore


class Database:
    """Encapsulates async SQLAlchemy engine and session handling."""

    def __init__(self, database_url: str | None = None):
        # database_url may come from settings; keep line short for lint.
        self.database_url = (
            database_url or settings.database_url  # type: ignore[attr-defined]
        )
        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
            poolclass=(
                StaticPool if self.database_url.endswith(":memory:") else None
            ),
            connect_args={"check_same_thread": False}
            if self.database_url.startswith("sqlite")
            else {},
        )
        session_maker = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        self._session_factory = session_maker

    async def create_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session: AsyncSession = self._session_factory()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()

    @property
    def engine(self):  # pragma: no cover
        return self._engine


# Module-level convenience functions
_default_database: Database | None = None


def get_database() -> Database:
    """Get or create the default database instance."""
    global _default_database
    if _default_database is None:
        _default_database = Database()
    return _default_database


async def init_database() -> Database:
    """Initialize the database and create tables."""
    db = get_database()
    await db.create_tables()
    return db


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI - yields async session."""
    db = get_database()
    async with db.session() as session:
        yield session


__all__ = ["Database", "get_database", "init_database", "get_async_session"]
