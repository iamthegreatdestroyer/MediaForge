"""Database base classes and mixins for MediaForge.

Provides SQLAlchemy 2.0 declarative base along with common UUID primary key
and timestamp mixins used across all ORM models.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4
from typing import Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime


class Base(DeclarativeBase):
    """Root declarative base class for all ORM models."""


class TimestampMixin:
    """Mixin adding creation and modification timestamps.

    Attributes:
        created_at: UTC timestamp when the row was inserted.
        modified_at: UTC timestamp when the row was last updated.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class UUIDMixin:
    """Mixin adding a UUID primary key column named ``id``."""

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


__all__ = ["Base", "TimestampMixin", "UUIDMixin"]
