"""Database base classes and mixins for MediaForge.

Provides SQLAlchemy 2.0 declarative base along with common UUID primary key
and timestamp mixins used across all ORM models.
"""

from __future__ import annotations

from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, String


class Base(DeclarativeBase):
    """Root declarative base class for all ORM models."""


class TimestampMixin:
    """Mixin adding creation and modification timestamps.

    Attributes:
        created_at: UTC timestamp when the row was inserted.
        modified_at: UTC timestamp when the row was last updated.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )


class UUIDMixin:
    """Mixin adding a UUID (stored as string) primary key column named ``id``.

    Uses a 36-character string representation to ensure broad SQLite compatibility.
    """

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))


__all__ = ["Base", "TimestampMixin", "UUIDMixin"]
