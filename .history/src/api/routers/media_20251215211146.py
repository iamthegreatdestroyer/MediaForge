"""Media endpoints router."""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    MediaResponse,
    CreateMediaRequest,
    UpdateMediaRequest,
    ErrorResponse,
)
from src.api.app import get_db
from src.core.database import Database
from src.repositories.media import MediaRepository

router = APIRouter()


async def get_media_repo(db: Database = Depends(get_db)) -> MediaRepository:
    """Dependency: Get media repository.
    
    Args:
        db: Database instance
        
    Yields:
        MediaRepository instance
    """
    async with db.session() as session:
        yield MediaRepository(session)


# ============================================================================
# CRUD Endpoints
# ============================================================================

@router.get("/", response_model=List[MediaResponse])
async def list_media(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: MediaRepository = Depends(get_media_repo),
) -> List[MediaResponse]:
    """Get paginated list of media items.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
        repo: Media repository
        
    Returns:
        List of media items
    """
    media_items = await repo.get_all(skip=skip, limit=limit)
    return [MediaResponse.from_orm(item) for item in media_items]


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media(
    media_id: str,
    repo: MediaRepository = Depends(get_media_repo),
) -> MediaResponse:
    """Get specific media item by ID.
    
    Args:
        media_id: Media item ID
        repo: Media repository
        
    Returns:
        Media item details
        
    Raises:
        HTTPException: If media not found
    """
    media = await repo.get_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return MediaResponse.from_orm(media)


@router.post("/", response_model=MediaResponse, status_code=201)
async def create_media(
    request: CreateMediaRequest,
    repo: MediaRepository = Depends(get_media_repo),
) -> MediaResponse:
    """Create new media entry for file.
    
    Args:
        request: Media creation request
        repo: Media repository
        
    Returns:
        Created media item
        
    Raises:
        HTTPException: If file not found or already exists
    """
    from pathlib import Path
    from src.core.hasher import calculate_hash
    
    # Validate file exists
    file_path = Path(request.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=400, detail="File not found")
    
    # Calculate hash
    file_hash = await calculate_hash(str(file_path))
    
    # Check for duplicates
    existing = await repo.find_by_hash(file_hash)
    if existing:
        raise HTTPException(status_code=409, detail="Duplicate file already exists")
    
    # Create media item
    from src.models.media import MediaItem
    media = MediaItem(
        file_path=str(file_path),
        file_hash=file_hash,
        file_size=file_path.stat().st_size,
        media_type="unknown",  # Would be detected in real implementation
    )
    
    created = await repo.create(media)
    await repo.commit()
    
    return MediaResponse.from_orm(created)


@router.patch("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: str,
    request: UpdateMediaRequest,
    repo: MediaRepository = Depends(get_media_repo),
) -> MediaResponse:
    """Update media item.
    
    Args:
        media_id: Media item ID
        request: Update request
        repo: Media repository
        
    Returns:
        Updated media item
        
    Raises:
        HTTPException: If media not found
    """
    media = await repo.get_by_id(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # Apply updates
    if request.filename:
        media.filename = request.filename
    
    updated = await repo.update(media)
    await repo.commit()
    
    return MediaResponse.from_orm(updated)


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: str,
    repo: MediaRepository = Depends(get_media_repo),
) -> None:
    """Delete media item.
    
    Args:
        media_id: Media item ID
        repo: Media repository
        
    Raises:
        HTTPException: If media not found
    """
    deleted = await repo.delete(media_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Media not found")
    
    await repo.commit()


# ============================================================================
# Query Endpoints
# ============================================================================

@router.get("/hash/{file_hash}", response_model=MediaResponse | None)
async def find_by_hash(
    file_hash: str,
    repo: MediaRepository = Depends(get_media_repo),
) -> MediaResponse | None:
    """Find media by file hash.
    
    Args:
        file_hash: SHA-256 file hash
        repo: Media repository
        
    Returns:
        Media item if found, None otherwise
    """
    media = await repo.find_by_hash(file_hash)
    return MediaResponse.from_orm(media) if media else None


@router.get("/type/{media_type}", response_model=List[MediaResponse])
async def find_by_type(
    media_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: MediaRepository = Depends(get_media_repo),
) -> List[MediaResponse]:
    """Find media by type.
    
    Args:
        media_type: Type of media (image, video, audio, etc)
        skip: Pagination offset
        limit: Pagination limit
        repo: Media repository
        
    Returns:
        List of media items of specified type
    """
    media_items = await repo.find_by_media_type(media_type)
    paginated = media_items[skip : skip + limit]
    return [MediaResponse.from_orm(item) for item in paginated]


@router.get("/recent/", response_model=List[MediaResponse])
async def get_recent(
    limit: int = Query(50, ge=1, le=1000),
    repo: MediaRepository = Depends(get_media_repo),
) -> List[MediaResponse]:
    """Get recently added media items.
    
    Args:
        limit: Maximum number of items
        repo: Media repository
        
    Returns:
        List of recent media items
    """
    media_items = await repo.find_recent(limit=limit)
    return [MediaResponse.from_orm(item) for item in media_items]


@router.get("/duplicates/", response_model=dict)
async def find_duplicates(
    repo: MediaRepository = Depends(get_media_repo),
) -> dict:
    """Find duplicate media files.
    
    Args:
        repo: Media repository
        
    Returns:
        Dictionary with duplicate groups
    """
    duplicates = await repo.find_duplicates()
    return {
        "duplicates": [
            {
                "hash": file_hash,
                "count": len(items),
                "media": [MediaResponse.from_orm(item).model_dump() for item in items],
            }
            for file_hash, items in duplicates
        ],
        "total_groups": len(duplicates),
    }


@router.get("/stats/", response_model=dict)
async def get_statistics(
    repo: MediaRepository = Depends(get_media_repo),
) -> dict:
    """Get media library statistics.
    
    Args:
        repo: Media repository
        
    Returns:
        Statistics about media collection
    """
    stats = await repo.get_statistics()
    return stats
