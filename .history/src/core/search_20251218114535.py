"""Full-text search using SQLite FTS5.

Provides fast, fuzzy text search across media items using SQLite's
FTS5 extension for sub-linear search performance.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with relevance scoring.
    
    Attributes:
        media_id: ID of matching media item
        file_path: Path to the file
        file_name: Name of the file
        media_type: Type of media
        rank: FTS5 relevance score (lower is better)
        snippet: Text snippet with highlighted matches
    """
    media_id: str
    file_path: str
    file_name: str
    media_type: str
    rank: float
    snippet: str = ""


class FTSSearchEngine:
    """Full-text search engine using SQLite FTS5.
    
    Provides fast, fuzzy text search across media items with:
    - Full-text indexing of file names, paths, and metadata
    - Fuzzy matching with prefix/suffix wildcards
    - Relevance ranking (BM25 algorithm)
    - Snippet generation with highlights
    
    Example:
        >>> engine = FTSSearchEngine(session)
        >>> await engine.ensure_fts_table()
        >>> results = await engine.search("vacation photos")
    """
    
    # FTS5 virtual table name
    FTS_TABLE = "media_search_fts"
    
    def __init__(self, session: AsyncSession):
        """Initialize the search engine.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def ensure_fts_table(self) -> None:
        """Create the FTS5 virtual table if it doesn't exist.
        
        This should be called during database initialization.
        """
        # Create FTS5 virtual table
        create_fts_sql = f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.FTS_TABLE} USING fts5(
                media_id UNINDEXED,
                file_name,
                file_path,
                media_type,
                mime_type,
                tags,
                caption,
                tokenize = 'porter unicode61 remove_diacritics 2',
                content = '',
                contentless_delete = 1
            )
        """
        
        await self.session.execute(text(create_fts_sql))
        await self.session.commit()
        
        logger.info(f"FTS5 table '{self.FTS_TABLE}' ensured")
    
    async def index_media_item(
        self,
        media_id: str,
        file_name: str,
        file_path: str,
        media_type: str,
        mime_type: str = "",
        tags: List[str] | None = None,
        caption: str = ""
    ) -> None:
        """Index a media item for full-text search.
        
        Args:
            media_id: Unique identifier
            file_name: Name of the file
            file_path: Path to the file
            media_type: Type of media (video, audio, image)
            mime_type: MIME type
            tags: List of tags
            caption: Generated caption/description
        """
        # Join tags into searchable string
        tags_str = " ".join(tags) if tags else ""
        
        # Insert into FTS table
        insert_sql = f"""
            INSERT INTO {self.FTS_TABLE}(
                media_id, file_name, file_path, media_type, 
                mime_type, tags, caption
            ) VALUES (
                :media_id, :file_name, :file_path, :media_type,
                :mime_type, :tags, :caption
            )
        """
        
        await self.session.execute(
            text(insert_sql),
            {
                "media_id": media_id,
                "file_name": file_name,
                "file_path": file_path,
                "media_type": media_type,
                "mime_type": mime_type,
                "tags": tags_str,
                "caption": caption,
            }
        )
        
        logger.debug(f"Indexed media item: {file_name}")
    
    async def remove_from_index(self, media_id: str) -> None:
        """Remove a media item from the search index.
        
        Args:
            media_id: ID of media item to remove
        """
        delete_sql = f"""
            DELETE FROM {self.FTS_TABLE} WHERE media_id = :media_id
        """
        
        await self.session.execute(
            text(delete_sql),
            {"media_id": media_id}
        )
        
        logger.debug(f"Removed from index: {media_id}")
    
    async def search(
        self,
        query: str,
        media_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SearchResult]:
        """Search for media items matching the query.
        
        Args:
            query: Search query (supports FTS5 syntax)
            media_type: Filter by media type (video, audio, image)
            limit: Maximum results to return
            offset: Number of results to skip
            
        Returns:
            List of search results sorted by relevance
        """
        if not query.strip():
            return []
        
        # Sanitize and prepare query for FTS5
        fts_query = self._prepare_query(query)
        
        # Build search SQL with optional type filter
        type_filter = ""
        params = {
            "query": fts_query,
            "limit": limit,
            "offset": offset,
        }
        
        if media_type:
            type_filter = "AND media_type = :media_type"
            params["media_type"] = media_type
        
        search_sql = f"""
            SELECT 
                media_id,
                file_name,
                file_path,
                media_type,
                rank,
                snippet({self.FTS_TABLE}, 1, '<b>', '</b>', '...', 32) as snippet
            FROM {self.FTS_TABLE}
            WHERE {self.FTS_TABLE} MATCH :query
            {type_filter}
            ORDER BY rank
            LIMIT :limit OFFSET :offset
        """
        
        result = await self.session.execute(text(search_sql), params)
        rows = result.fetchall()
        
        return [
            SearchResult(
                media_id=row[0],
                file_name=row[1],
                file_path=row[2],
                media_type=row[3],
                rank=row[4],
                snippet=row[5] or "",
            )
            for row in rows
        ]
    
    async def search_count(
        self,
        query: str,
        media_type: Optional[str] = None
    ) -> int:
        """Count total matching results for a query.
        
        Args:
            query: Search query
            media_type: Optional type filter
            
        Returns:
            Total count of matching items
        """
        if not query.strip():
            return 0
        
        fts_query = self._prepare_query(query)
        
        type_filter = ""
        params = {"query": fts_query}
        
        if media_type:
            type_filter = "AND media_type = :media_type"
            params["media_type"] = media_type
        
        count_sql = f"""
            SELECT COUNT(*)
            FROM {self.FTS_TABLE}
            WHERE {self.FTS_TABLE} MATCH :query
            {type_filter}
        """
        
        result = await self.session.execute(text(count_sql), params)
        return result.scalar() or 0
    
    async def suggest(
        self,
        prefix: str,
        limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions for a prefix.
        
        Args:
            prefix: Text prefix to complete
            limit: Maximum suggestions
            
        Returns:
            List of suggested completions
        """
        if not prefix.strip() or len(prefix) < 2:
            return []
        
        # Use prefix search
        fts_query = f"{prefix}*"
        
        suggest_sql = f"""
            SELECT DISTINCT file_name
            FROM {self.FTS_TABLE}
            WHERE {self.FTS_TABLE} MATCH :query
            LIMIT :limit
        """
        
        result = await self.session.execute(
            text(suggest_sql),
            {"query": fts_query, "limit": limit}
        )
        
        return [row[0] for row in result.fetchall()]
    
    async def reindex_all(self) -> int:
        """Rebuild the entire FTS index from media_items table.
        
        Returns:
            Number of items indexed
        """
        # Clear existing index
        await self.session.execute(text(f"DELETE FROM {self.FTS_TABLE}"))
        
        # Re-index all media items
        reindex_sql = f"""
            INSERT INTO {self.FTS_TABLE}(
                media_id, file_name, file_path, media_type, mime_type, tags, caption
            )
            SELECT 
                CAST(m.id AS TEXT),
                m.file_name,
                m.file_path,
                m.media_type,
                m.mime_type,
                COALESCE(
                    (SELECT GROUP_CONCAT(t.name, ' ') 
                     FROM media_item_tags mt 
                     JOIN tags t ON mt.tag_id = t.id 
                     WHERE mt.media_item_id = m.id),
                    ''
                ),
                COALESCE(mm.caption, '')
            FROM media_items m
            LEFT JOIN media_metadata mm ON m.id = mm.media_item_id
        """
        
        await self.session.execute(text(reindex_sql))
        
        # Get count
        count_result = await self.session.execute(
            text(f"SELECT COUNT(*) FROM {self.FTS_TABLE}")
        )
        count = count_result.scalar() or 0
        
        await self.session.commit()
        
        logger.info(f"Reindexed {count} media items")
        return count
    
    def _prepare_query(self, query: str) -> str:
        """Prepare a user query for FTS5 search.
        
        Handles:
        - Escaping special characters
        - Adding prefix matching for partial words
        - Handling quoted phrases
        
        Args:
            query: Raw user query
            
        Returns:
            FTS5-compatible query string
        """
        # Preserve quoted phrases
        phrases = re.findall(r'"[^"]*"', query)
        
        # Remove phrases from query temporarily
        remaining = re.sub(r'"[^"]*"', '', query)
        
        # Escape special FTS5 characters
        special_chars = ['*', '(', ')', '"', '-', '^']
        for char in special_chars:
            remaining = remaining.replace(char, ' ')
        
        # Split into words and add prefix matching
        words = remaining.split()
        processed_words = []
        
        for word in words:
            word = word.strip()
            if word and len(word) >= 2:
                # Add prefix matching for partial word search
                processed_words.append(f"{word}*")
        
        # Combine with preserved phrases
        parts = processed_words + phrases
        
        if not parts:
            return ""
        
        # Join with OR for broader matching
        return " OR ".join(parts)


async def create_fts_search_engine(session: AsyncSession) -> FTSSearchEngine:
    """Factory function to create and initialize FTS search engine.
    
    Args:
        session: SQLAlchemy async session
        
    Returns:
        Initialized FTSSearchEngine
    """
    engine = FTSSearchEngine(session)
    await engine.ensure_fts_table()
    return engine
