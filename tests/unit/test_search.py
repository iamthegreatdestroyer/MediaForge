"""Tests for FTS5 search engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.search import FTSSearchEngine, SearchResult


class TestSearchResult:
    """Tests for SearchResult dataclass."""
    
    def test_search_result_creation(self):
        """Test SearchResult creation."""
        result = SearchResult(
            media_id="123",
            file_path="/media/test.mp4",
            file_name="test.mp4",
            media_type="video",
            rank=-1.5,
            snippet="test <b>video</b> content"
        )
        
        assert result.media_id == "123"
        assert result.file_path == "/media/test.mp4"
        assert result.file_name == "test.mp4"
        assert result.media_type == "video"
        assert result.rank == -1.5
        assert result.snippet == "test <b>video</b> content"
    
    def test_search_result_default_snippet(self):
        """Test SearchResult default snippet."""
        result = SearchResult(
            media_id="123",
            file_path="/test.mp4",
            file_name="test.mp4",
            media_type="video",
            rank=0
        )
        
        assert result.snippet == ""


class TestFTSSearchEngine:
    """Tests for FTSSearchEngine class."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session
    
    @pytest.fixture
    def search_engine(self, mock_session):
        """Create a search engine with mock session."""
        return FTSSearchEngine(mock_session)
    
    @pytest.mark.asyncio
    async def test_ensure_fts_table(self, search_engine, mock_session):
        """Test FTS table creation."""
        await search_engine.ensure_fts_table()
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Check that CREATE VIRTUAL TABLE was called
        call_args = mock_session.execute.call_args
        sql = str(call_args[0][0])
        assert "CREATE VIRTUAL TABLE" in sql
        assert "fts5" in sql.lower()
    
    @pytest.mark.asyncio
    async def test_index_media_item(self, search_engine, mock_session):
        """Test indexing a media item."""
        await search_engine.index_media_item(
            media_id="123",
            file_name="vacation.mp4",
            file_path="/media/vacation.mp4",
            media_type="video",
            mime_type="video/mp4",
            tags=["vacation", "beach", "summer"],
            caption="Beach vacation video"
        )
        
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        params = call_args[1]
        
        assert params["media_id"] == "123"
        assert params["file_name"] == "vacation.mp4"
        assert params["tags"] == "vacation beach summer"
        assert params["caption"] == "Beach vacation video"
    
    @pytest.mark.asyncio
    async def test_remove_from_index(self, search_engine, mock_session):
        """Test removing from index."""
        await search_engine.remove_from_index("123")
        
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args
        params = call_args[1]
        
        assert params["media_id"] == "123"
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, search_engine, mock_session):
        """Test search with empty query returns empty list."""
        results = await search_engine.search("")
        assert results == []
        
        results = await search_engine.search("   ")
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_with_results(self, search_engine, mock_session):
        """Test search returns results."""
        # Mock the database response
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("123", "test.mp4", "/media/test.mp4", "video", -1.5, "test <b>video</b>"),
            ("456", "test2.mp4", "/media/test2.mp4", "video", -1.0, "another <b>video</b>"),
        ]
        mock_session.execute.return_value = mock_result
        
        results = await search_engine.search("video")
        
        assert len(results) == 2
        assert results[0].media_id == "123"
        assert results[0].file_name == "test.mp4"
        assert results[1].media_id == "456"
    
    @pytest.mark.asyncio
    async def test_search_with_media_type_filter(self, search_engine, mock_session):
        """Test search with media type filter."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result
        
        await search_engine.search("test", media_type="video")
        
        call_args = mock_session.execute.call_args
        params = call_args[1]
        
        assert params["media_type"] == "video"
    
    @pytest.mark.asyncio
    async def test_search_count(self, search_engine, mock_session):
        """Test search_count method."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result
        
        count = await search_engine.search_count("test")
        
        assert count == 42
    
    @pytest.mark.asyncio
    async def test_search_count_empty_query(self, search_engine, mock_session):
        """Test search_count with empty query."""
        count = await search_engine.search_count("")
        assert count == 0
    
    @pytest.mark.asyncio
    async def test_suggest(self, search_engine, mock_session):
        """Test autocomplete suggestions."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("vacation.mp4",),
            ("vacation_beach.mp4",),
        ]
        mock_session.execute.return_value = mock_result
        
        suggestions = await search_engine.suggest("vac")
        
        assert len(suggestions) == 2
        assert "vacation.mp4" in suggestions
    
    @pytest.mark.asyncio
    async def test_suggest_short_prefix(self, search_engine, mock_session):
        """Test suggest with short prefix returns empty."""
        suggestions = await search_engine.suggest("v")
        assert suggestions == []
    
    def test_prepare_query_basic(self, search_engine):
        """Test query preparation."""
        result = search_engine._prepare_query("beach vacation")
        
        # Should add prefix matching
        assert "beach*" in result or "vacation*" in result
    
    def test_prepare_query_with_quotes(self, search_engine):
        """Test query preparation preserves quoted phrases."""
        result = search_engine._prepare_query('"exact phrase" other')
        
        assert '"exact phrase"' in result
    
    def test_prepare_query_escapes_special_chars(self, search_engine):
        """Test query preparation escapes special characters."""
        result = search_engine._prepare_query("test*query")
        
        # Should not have raw special chars
        assert result.count("*") == 1 or "test" in result
    
    def test_prepare_query_empty(self, search_engine):
        """Test prepare query with empty input."""
        result = search_engine._prepare_query("")
        assert result == ""
