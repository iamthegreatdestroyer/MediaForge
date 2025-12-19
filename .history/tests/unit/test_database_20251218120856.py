"""Tests for database module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.core.database import Database


class TestDatabase:
    """Tests for Database class."""
    
    @pytest.fixture
    def sqlite_memory_db(self):
        """Create an in-memory SQLite database."""
        return Database("sqlite+aiosqlite:///:memory:")
    
    def test_database_initialization(self, sqlite_memory_db):
        """Test database initialization."""
        assert sqlite_memory_db.database_url == "sqlite+aiosqlite:///:memory:"
        assert sqlite_memory_db._engine is not None
        assert sqlite_memory_db._session_factory is not None
    
    def test_database_with_custom_url(self):
        """Test database with custom URL."""
        custom_url = "sqlite+aiosqlite:///test.db"
        db = Database(custom_url)
        
        assert db.database_url == custom_url
    
    @pytest.mark.asyncio
    async def test_create_tables(self, sqlite_memory_db):
        """Test creating database tables."""
        await sqlite_memory_db.create_tables()
        # If no exception, tables were created successfully
    
    @pytest.mark.asyncio
    async def test_drop_tables(self, sqlite_memory_db):
        """Test dropping database tables."""
        await sqlite_memory_db.create_tables()
        await sqlite_memory_db.drop_tables()
        # If no exception, tables were dropped successfully
    
    @pytest.mark.asyncio
    async def test_session_context_manager(self, sqlite_memory_db):
        """Test session context manager."""
        await sqlite_memory_db.create_tables()
        
        async with sqlite_memory_db.session() as session:
            assert session is not None
            # Session should be usable
            result = await session.execute(
                "SELECT 1"
            )
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_session_commits_on_success(self, sqlite_memory_db):
        """Test session commits on successful exit."""
        await sqlite_memory_db.create_tables()
        
        # Create a mock session to track commits
        with patch.object(sqlite_memory_db, '_session_factory') as mock_factory:
            mock_session = AsyncMock()
            mock_factory.return_value = mock_session
            
            async with sqlite_memory_db.session():
                pass
            
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self, sqlite_memory_db):
        """Test session rollback on SQLAlchemy error."""
        from sqlalchemy.exc import SQLAlchemyError
        
        await sqlite_memory_db.create_tables()
        
        with patch.object(sqlite_memory_db, '_session_factory') as mock_factory:
            mock_session = AsyncMock()
            mock_session.commit.side_effect = SQLAlchemyError("Test error")
            mock_factory.return_value = mock_session
            
            with pytest.raises(SQLAlchemyError):
                async with sqlite_memory_db.session():
                    pass
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_engine_property(self, sqlite_memory_db):
        """Test engine property."""
        engine = sqlite_memory_db.engine
        assert engine is not None
        assert engine is sqlite_memory_db._engine
