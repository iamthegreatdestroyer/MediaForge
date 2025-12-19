"""
AI-powered CLI commands for auto-tagging and semantic search
"""

import asyncio
import click
import json
from typing import Optional
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Database
from src.core.auto_tagger import get_auto_tagger
from src.core.semantic_search import get_search_engine
from src.core.ai_engine import get_ai_engine
from src.models.media import MediaItem
from src.cli.display import display_info, display_success, display_warning, display_error


@click.group()
def ai() -> None:
    """AI-powered media management commands"""
    pass


@ai.command()
@click.option(
    "--media-id",
    type=str,
    default=None,
    help="Tag specific media (by ID)"
)
@click.option(
    "--all",
    is_flag=True,
    help="Tag all untagged media"
)
@click.option(
    "--use-visual",
    is_flag=True,
    default=True,
    help="Analyze images visually"
)
@click.option(
    "--batch-size",
    type=int,
    default=5,
    help="Batch size for parallel processing"
)
def tag(
    media_id: Optional[str],
    all: bool,
    use_visual: bool,
    batch_size: int
) -> None:
    """
    Generate AI tags for media items
    
    Examples:
      mediaforge ai tag --media-id <id>      # Tag specific media
      mediaforge ai tag --all                 # Tag all untagged media
      mediaforge ai tag --all --batch-size 10 # Faster processing
    """
    
    async def _tag():
        db = Database()
        async with db.session() as session:
            tagger = get_auto_tagger(session)
            
            # Verify AI engine is available
            if not get_ai_engine().is_available():
                display_error("❌ AI Engine not available!")
                return
            
            display_info("🤖 AI Tagging Service")
            display_info("-" * 50)
            
            if media_id:
                # Tag specific media
                display_info(f"Tagging media: {media_id}")
                result = await tagger.regenerate_tags_for_media(media_id)
                
                if result["status"] == "success":
                    display_success(f"✅ Tagged with {result['tags_count']} tags")
                    for tag in result.get("tags", []):
                        click.echo(f"   - {tag}")
                else:
                    display_error(f"❌ Failed: {result.get('error', 'Unknown error')}")
            
            elif all:
                # Tag all untagged media
                display_info("Finding untagged media...")
                result = await tagger.process_untagged(use_visual=use_visual)
                
                display_info(f"Processing {result['processed']} items...")
                display_success(f"✅ Completed: {result['successes']}/{result['processed']} successful")
            
            else:
                display_warning("⚠️  Specify --media-id <id> or --all")
    
    asyncio.run(_tag())


@ai.command()
@click.argument("query")
@click.option(
    "--top-k",
    type=int,
    default=20,
    help="Number of results"
)
@click.option(
    "--threshold",
    type=float,
    default=0.0,
    help="Minimum similarity threshold (0-1)"
)
def search(query: str, top_k: int, threshold: float) -> None:
    """
    Search media semantically
    
    Uses AI embeddings to find similar media.
    Much more powerful than keyword search!
    
    Examples:
      mediaforge ai search "sunset landscape"
      mediaforge ai search "nature" --top-k 50
      mediaforge ai search "blue water" --threshold 0.5
    """
    
    async def _search():
        db = Database()
        async with db.session() as session:
            display_info("🔍 Semantic Search")
            display_info("-" * 50)
            display_info(f"Query: {query}")
            display_info(f"Top K: {top_k}, Threshold: {threshold}")
            display_info("")
            
            # Fetch all indexed media
            stmt = select(MediaItem).where(
                MediaItem.semantic_embedding.isnot(None)
            )
            result = await session.execute(stmt)
            all_media = result.scalars().all()
            
            if not all_media:
                display_warning("⚠️  No indexed media found. Run 'ai tag --all' first.")
                return
            
            # Reconstruct embeddings
            embeddings_list = []
            for media in all_media:
                from src.core.ai_engine import AIEngine
                embedding = AIEngine.bytes_to_embedding(media.semantic_embedding)
                embeddings_list.append(embedding)
            
            import numpy as np
            embeddings = np.array(embeddings_list)
            
            # Perform search
            search_engine = get_search_engine()
            results = search_engine.search_semantic(
                query,
                embeddings,
                all_media,
                top_k=top_k,
                similarity_threshold=threshold
            )
            
            if not results:
                display_warning("⚠️  No results found")
                return
            
            display_success(f"Found {len(results)} results:")
            display_info("")
            
            for i, result in enumerate(results, 1):
                similarity = round(result.similarity_score * 100, 1)
                display_info(f"{i}. {result.media.file_name}")
                display_info(f"   Similarity: {similarity}%")
                
                # Show AI tags if available
                if result.media.ai_tags:
                    try:
                        tags = json.loads(result.media.ai_tags) if isinstance(result.media.ai_tags, str) else result.media.ai_tags
                        if isinstance(tags, list) and len(tags) > 0:
                            tag_str = ", ".join(tags[:3])
                            if len(tags) > 3:
                                tag_str += f", +{len(tags) - 3} more"
                            display_info(f"   Tags: {tag_str}")
                    except:
                        pass
                
                display_info("")
    
    asyncio.run(_search())


@ai.command()
@click.option(
    "--min-size",
    type=int,
    default=3,
    help="Minimum collection size"
)
def collections(min_size: int) -> None:
    """
    Discover automatic semantic collections
    
    Uses clustering to find groups of similar media.
    
    Examples:
      mediaforge ai collections
      mediaforge ai collections --min-size 5
    """
    
    async def _collections():
        db = Database()
        async with db.session() as session:
            display_info("🎯 Auto-Discovered Collections")
            display_info("-" * 50)
            
            # Fetch all indexed media
            stmt = select(MediaItem).where(
                MediaItem.semantic_embedding.isnot(None)
            )
            result = await session.execute(stmt)
            all_media = result.scalars().all()
            
            if len(all_media) < min_size:
                display_warning(
                    f"⚠️  Not enough media ({len(all_media)}) "
                    f"to form collections. Need at least {min_size}."
                )
                return
            
            # Reconstruct embeddings
            embeddings_list = []
            for media in all_media:
                from src.core.ai_engine import AIEngine
                embedding = AIEngine.bytes_to_embedding(media.semantic_embedding)
                embeddings_list.append(embedding)
            
            import numpy as np
            embeddings = np.array(embeddings_list)
            
            # Perform clustering
            search_engine = get_search_engine()
            clusters = search_engine.cluster_embeddings(embeddings, all_media)
            
            # Filter and sort
            filtered = [
                (cid, items) 
                for cid, items in clusters.items() 
                if len(items) >= min_size
            ]
            filtered.sort(key=lambda x: len(x[1]), reverse=True)
            
            if not filtered:
                display_warning(
                    f"⚠️  No collections found with minimum size {min_size}"
                )
                return
            
            display_success(f"Found {len(filtered)} collections:")
            display_info("")
            
            for i, (cluster_id, items) in enumerate(filtered, 1):
                display_info(f"{i}. Cluster #{cluster_id} ({len(items)} items)")
                
                # Show sample files
                for j, item in enumerate(items[:3]):
                    display_info(f"   - {item.file_name}")
                
                if len(items) > 3:
                    display_info(f"   ... and {len(items) - 3} more")
                
                display_info("")
    
    asyncio.run(_collections())


@ai.command()
def status() -> None:
    """
    Show AI engine status
    
    Displays embeddings, model availability, and statistics.
    """
    
    async def _status():
        db = Database()
        async with db.session() as session:
            display_info("🤖 AI Engine Status")
            display_info("-" * 50)
            
            # Check AI engine
            ai = get_ai_engine()
            if ai.is_available():
                display_success("✅ AI Engine: Ready")
            else:
                display_error("❌ AI Engine: Not available")
            
            # Ollama status
            if ai.ollama:
                display_success("✅ Ollama: Connected")
                models = ai.get_available_models()
                available = models.get("available", [])
                if available:
                    display_info(f"   Models: {len(available)}")
            else:
                display_warning("⚠️  Ollama: Offline (will use local models)")
            
            # Embeddings
            if ai.embeddings_model:
                display_success("✅ Embeddings: Loaded")
            else:
                display_warning("⚠️  Embeddings: Not available")
            
            display_info("")
            
            # Statistics
            display_info("📊 Indexing Statistics:")
            
            tagged_stmt = select(MediaItem).where(
                MediaItem.embedding_processed_at.isnot(None)
            )
            tagged_result = await session.execute(tagged_stmt)
            tagged_count = len(tagged_result.scalars().all())
            
            untagged_stmt = select(MediaItem).where(
                MediaItem.embedding_processed_at.is_(None)
            )
            untagged_result = await session.execute(untagged_stmt)
            untagged_count = len(untagged_result.scalars().all())
            
            total = tagged_count + untagged_count
            
            if total == 0:
                display_warning("⚠️  No media in library")
            else:
                pct = round((tagged_count / total * 100), 1)
                display_info(f"   Total: {total} items")
                display_success(f"   Indexed: {tagged_count} ({pct}%)")
                display_warning(f"   Remaining: {untagged_count}")
    
    asyncio.run(_status())


__all__ = ["ai"]
