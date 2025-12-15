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
        self.database_url = database_url or settings.database_url  # type: ignore[attr-defined]
        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            future=True,
            poolclass=StaticPool if self.database_url.endswith(":memory:") else None,
            connect_args={"check_same_thread": False}
            if self.database_url.startswith("sqlite")
            else {},
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

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

__all__ = ["Database"]
