"""
Auto-Tagging Service - Generates and manages AI-driven tags for media
"""

import asyncio
import json
import logging
from datetime import datetime, UTC
from typing import List, Dict, Optional
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.models.media import MediaItem, Tag
from src.core.ai_engine import get_ai_engine, AIEngine
from src.core.semantic_search import get_search_engine

logger = logging.getLogger(__name__)


class AutoTagger:
    """
    Intelligent auto-tagging service using AI
    
    Features:
    - Batch processing for efficiency
    - Incremental tagging (only new media)
    - Visual analysis for images
    - Semantic embedding generation
    - Automatic tag creation
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize AutoTagger
        
        Args:
            db_session: SQLAlchemy async session
        """
        self.db = db_session
        self.ai_engine: AIEngine = get_ai_engine()
        self.search_engine = get_search_engine()
        
    async def process_media_batch(
        self,
        media_ids: List[str],
        use_visual: bool = True,
        skip_existing: bool = True,
        batch_size: int = 5
    ) -> Dict[str, dict]:
        """
        Process a batch of media items for tagging
        
        Args:
            media_ids: List of media IDs to process
            use_visual: Whether to analyze images visually
            skip_existing: Skip media that already has tags
            batch_size: Number of items to process in parallel
            
        Returns:
            Dictionary with results for each media ID
        """
        results = {}
        
        # Process in batches for efficiency
        for i in range(0, len(media_ids), batch_size):
            batch = media_ids[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} items")
            
            # Process each item in batch
            batch_results = await asyncio.gather(
                *[self._process_single_media(mid, use_visual, skip_existing)
                  for mid in batch],
                return_exceptions=True
            )
            
            # Collect results
            for media_id, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing {media_id}: {result}")
                    results[media_id] = {"status": "error", "error": str(result)}
                else:
                    results[media_id] = result
        
        return results
    
    async def _process_single_media(
        self,
        media_id: str,
        use_visual: bool = True,
        skip_existing: bool = True
    ) -> dict:
        """
        Process single media item for tagging
        
        Args:
            media_id: Media item ID
            use_visual: Analyze visually if image
            skip_existing: Skip if already tagged
            
        Returns:
            Processing result
        """
        try:
            # Fetch media from database
            stmt = select(MediaItem).where(MediaItem.id == media_id)
            result = await self.db.execute(stmt)
            media = result.scalar_one_or_none()
            
            if not media:
                return {"status": "not_found"}
            
            # Skip if already processed and skip_existing is True
            if skip_existing and media.embedding_processed_at is not None:
                return {"status": "skipped", "reason": "already_processed"}
            
            # Generate metadata text for tagging
            metadata_text = self._build_metadata_text(media)
            
            # Get visual context if image
            visual_context = ""
            if use_visual and media.media_type.value == "image" and media.file_path:
                visual_context = await self.ai_engine.analyze_image_async(media.file_path)
                logger.debug(f"Visual analysis for {media_id}: {visual_context[:100]}...")
            
            # Generate semantic embedding
            embeddings = self.ai_engine.generate_embeddings([metadata_text])
            embedding_bytes = self.ai_engine.embedding_to_bytes(embeddings[0])
            
            # Generate tags
            tags = await self.ai_engine.generate_tags_async(
                metadata_text,
                visual_context
            )
            
            # Update media in database
            await self.db.execute(
                update(MediaItem)
                .where(MediaItem.id == media_id)
                .values({
                    MediaItem.semantic_embedding: embedding_bytes,
                    MediaItem.embedding_version: "minilm-l6-v2",
                    MediaItem.ai_tags: json.dumps(tags) if tags else None,
                    MediaItem.visual_description: visual_context or None,
                    MediaItem.embedding_processed_at: datetime.now(UTC),
                })
            )
            
            await self.db.commit()
            
            logger.info(f"✅ Processed {media_id}: {len(tags)} tags generated")
            return {
                "status": "success",
                "tags_count": len(tags),
                "tags": tags,
                "has_visual": len(visual_context) > 0
            }
            
        except Exception as e:
            logger.error(f"Error processing media {media_id}: {e}", exc_info=True)
            await self.db.rollback()
            return {"status": "error", "error": str(e)}
    
    def _build_metadata_text(self, media: MediaItem) -> str:
        """
        Build text for embedding generation from media metadata
        
        Args:
            media: MediaItem instance
            
        Returns:
            Combined metadata text
        """
        parts = [media.file_name]
        
        if media.media_metadata and media.media_metadata.description:
            parts.append(media.media_metadata.description)
        
        if media.media_metadata and media.media_metadata.artist:
            parts.append(f"by {media.media_metadata.artist}")
        
        # Add existing tags
        if media.tags:
            tag_names = [tag.name for tag in media.tags]
            parts.append(", ".join(tag_names))
        
        return " ".join(parts)
    
    async def process_untagged(self, use_visual: bool = True) -> Dict[str, dict]:
        """
        Process all untagged media
        
        Args:
            use_visual: Whether to analyze images visually
            
        Returns:
            Dictionary with results
        """
        # Find all untagged media
        stmt = select(MediaItem.id).where(
            MediaItem.embedding_processed_at.is_(None)
        )
        result = await self.db.execute(stmt)
        untagged_ids = [row[0] for row in result.fetchall()]
        
        logger.info(f"Found {len(untagged_ids)} untagged media items")
        
        if not untagged_ids:
            return {"status": "complete", "processed": 0}
        
        # Process all untagged
        results = await self.process_media_batch(
            untagged_ids,
            use_visual=use_visual,
            skip_existing=False
        )
        
        # Count successes
        successes = sum(1 for r in results.values() if r.get("status") == "success")
        
        return {
            "status": "complete",
            "processed": len(untagged_ids),
            "successes": successes,
            "results": results
        }
    
    async def regenerate_tags_for_media(self, media_id: str) -> dict:
        """
        Regenerate tags for a specific media item
        
        Args:
            media_id: Media item ID
            
        Returns:
            Processing result
        """
        return await self._process_single_media(
            media_id,
            use_visual=True,
            skip_existing=False  # Force regeneration
        )
    
    async def get_media_tags(self, media_id: str) -> Optional[List[str]]:
        """
        Get AI-generated tags for a media item
        
        Args:
            media_id: Media item ID
            
        Returns:
            List of tags or None
        """
        stmt = select(MediaItem.ai_tags).where(MediaItem.id == media_id)
        result = await self.db.execute(stmt)
        tags_json = result.scalar_one_or_none()
        
        if tags_json:
            try:
                return json.loads(tags_json)
            except json.JSONDecodeError:
                logger.error(f"Invalid tags JSON for {media_id}")
        
        return None


def get_auto_tagger(db_session: AsyncSession) -> AutoTagger:
    """Factory function to create AutoTagger instance"""
    return AutoTagger(db_session)
