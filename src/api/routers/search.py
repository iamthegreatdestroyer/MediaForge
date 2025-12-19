"""
Semantic Search and AI Tagging API Routes
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.media import MediaItem
from src.core.auto_tagger import get_auto_tagger, AutoTagger
from src.core.semantic_search import get_search_engine
from src.core.database import Database

router = APIRouter(prefix="/api/v1/ai", tags=["AI Features"])


# Dependency to get database session
async def get_db_session() -> AsyncSession:
    """Get database session"""
    db = Database()
    async with db.session() as session:
        yield session


class SearchRequest:
    """Search request model"""
    def __init__(self, query: str, top_k: int = 20, similarity_threshold: float = 0.0):
        self.query = query
        self.top_k = min(top_k, 100)  # Max 100 results
        self.similarity_threshold = max(0.0, min(1.0, similarity_threshold))


class TagResponse:
    """Tag response model"""
    def __init__(self, media_id: str, tags: List[str]):
        self.media_id = media_id
        self.tags = tags


@router.post("/process-untagged")
async def process_untagged_media(
    use_visual: bool = Query(True, description="Analyze images visually"),
    background_tasks: BackgroundTasks = None,
    db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Process all untagged media items
    
    This endpoint will:
    1. Find all media without embeddings
    2. Generate embeddings and tags
    3. Store results in database
    
    Returns immediately with processing status.
    Check /ai/status for progress.
    """
    try:
        tagger = get_auto_tagger(db_session)
        
        # Run in background
        if background_tasks:
            background_tasks.add_task(
                tagger.process_untagged,
                use_visual=use_visual
            )
        
        return {
            "status": "processing_started",
            "message": "Media tagging process started in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tag-media/{media_id}")
async def tag_single_media(
    media_id: str,
    use_visual: bool = Query(True),
    db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Generate tags for a specific media item
    
    Returns immediately with tag results.
    """
    try:
        tagger = get_auto_tagger(db_session)
        result = await tagger.regenerate_tags_for_media(media_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return {
            "media_id": media_id,
            "status": result["status"],
            "tags": result.get("tags", []),
            "tags_count": result.get("tags_count", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/{media_id}")
async def get_media_tags(
    media_id: str,
    db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Get AI-generated tags for a media item
    """
    try:
        tagger = get_auto_tagger(db_session)
        tags = await tagger.get_media_tags(media_id)
        
        if tags is None:
            raise HTTPException(status_code=404, detail="Tags not found for media")
        
        return {
            "media_id": media_id,
            "tags": tags,
            "count": len(tags)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/semantic")
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(20, ge=1, le=100, description="Number of results"),
    similarity_threshold: float = Query(0.0, ge=0.0, le=1.0),
    db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Search media using semantic similarity
    
    Uses AI embeddings to find semantically similar media.
    Much more powerful than keyword search.
    
    Example: "sunset landscape" will find scenic/nature media
    """
    try:
        # Fetch all media with embeddings
        stmt = select(MediaItem).where(
            MediaItem.semantic_embedding.isnot(None)
        )
        result = await db_session.execute(stmt)
        all_media = result.scalars().all()
        
        if not all_media:
            return {
                "query": q,
                "results": [],
                "count": 0,
                "message": "No indexed media found"
            }
        
        # Reconstruct embeddings from storage
        embeddings_list = []
        for media in all_media:
            from src.core.ai_engine import AIEngine
            embedding = AIEngine.bytes_to_embedding(media.semantic_embedding)
            embeddings_list.append(embedding)
        
        import numpy as np
        all_embeddings = np.array(embeddings_list)
        
        # Perform search
        search_engine = get_search_engine()
        search_results = search_engine.search_semantic(
            q,
            all_embeddings,
            all_media,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        # Format results
        formatted_results = [
            {
                "id": result.media.id,
                "file_name": result.media.file_name,
                "file_path": result.media.file_path,
                "media_type": result.media.media_type.value,
                "similarity_score": round(result.similarity_score, 3),
                "rank": result.rank + 1,
                "tags": result.media.ai_tags if isinstance(result.media.ai_tags, list) else None
            }
            for result in search_results
        ]
        
        return {
            "query": q,
            "results": formatted_results,
            "count": len(formatted_results),
            "top_k": top_k,
            "threshold": similarity_threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/collections/auto")
async def get_auto_collections(
    min_size: int = Query(3, ge=1, description="Minimum collection size"),
    db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Get automatically discovered semantic collections
    
    Uses clustering to automatically group similar media.
    """
    try:
        # Fetch all media with embeddings
        stmt = select(MediaItem).where(
            MediaItem.semantic_embedding.isnot(None)
        )
        result = await db_session.execute(stmt)
        all_media = result.scalars().all()
        
        if len(all_media) < min_size:
            return {
                "collections": [],
                "count": 0,
                "message": f"Not enough media ({len(all_media)}) to form collections"
            }
        
        # Reconstruct embeddings
        embeddings_list = []
        for media in all_media:
            from src.core.ai_engine import AIEngine
            embedding = AIEngine.bytes_to_embedding(media.semantic_embedding)
            embeddings_list.append(embedding)
        
        import numpy as np
        all_embeddings = np.array(embeddings_list)
        
        # Perform clustering
        search_engine = get_search_engine()
        clusters = search_engine.cluster_embeddings(all_embeddings, all_media)
        
        # Filter by minimum size and format
        formatted_collections = []
        for cluster_id, media_list in clusters.items():
            if len(media_list) >= min_size:
                formatted_collections.append({
                    "id": f"cluster_{cluster_id}",
                    "size": len(media_list),
                    "media_ids": [m.id for m in media_list],
                    "media_count": len(media_list)
                })
        
        # Sort by size (largest first)
        formatted_collections.sort(key=lambda x: x["size"], reverse=True)
        
        return {
            "collections": formatted_collections,
            "count": len(formatted_collections),
            "total_media": len(all_media),
            "min_size": min_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering error: {str(e)}")


@router.get("/status")
async def get_ai_status(
    db_session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Get AI engine status and statistics
    """
    try:
        # Count tagged vs untagged
        tagged_stmt = select(MediaItem).where(
            MediaItem.embedding_processed_at.isnot(None)
        )
        tagged_result = await db_session.execute(tagged_stmt)
        tagged_count = len(tagged_result.scalars().all())
        
        untagged_stmt = select(MediaItem).where(
            MediaItem.embedding_processed_at.is_(None)
        )
        untagged_result = await db_session.execute(untagged_stmt)
        untagged_count = len(untagged_result.scalars().all())
        
        # Get AI engine status
        from src.core.ai_engine import get_ai_engine
        ai = get_ai_engine()
        
        return {
            "ai_engine_ready": ai.is_available(),
            "ollama_connected": ai.ollama is not None,
            "embeddings_model_ready": ai.embeddings_model is not None,
            "statistics": {
                "total_media": tagged_count + untagged_count,
                "tagged": tagged_count,
                "untagged": untagged_count,
                "tagging_percentage": round((tagged_count / (tagged_count + untagged_count) * 100), 1) 
                                     if (tagged_count + untagged_count) > 0 else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
