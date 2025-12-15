"""Alembic environment file configured for MediaForge.

Supports offline and online migrations. Uses synchronous engine for migrations
even though application runtime uses async drivers.
"""

from __future__ import annotations

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

from src.models import Base
from src.core.config import settings  # type: ignore

# This config object provides access to values within the .ini file.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def _sync_database_url() -> str:
    url = settings.database_url  # type: ignore[attr-defined]
    # Convert async driver to sync for migrations.
    return url.replace("+aiosqlite", "")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite compatibility
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _sync_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():  # pragma: no cover
    run_migrations_offline()
else:  # pragma: no cover
    run_migrations_online()