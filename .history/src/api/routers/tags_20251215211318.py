"""Tag endpoints router."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.schemas import TagResponse, CreateTagRequest, UpdateTagRequest
from src.api.app import get_db
from src.core.database import Database
from src.repositories.tag import TagRepository

router = APIRouter()


async def get_tag_repo(db: Database = Depends(get_db)) -> TagRepository:
    """Dependency: Get tag repository."""
    async with db.session() as session:
        yield TagRepository(session)


@router.get("/", response_model=List[TagResponse])
async def list_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: TagRepository = Depends(get_tag_repo),
) -> List[TagResponse]:
    """Get paginated list of tags.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
        repo: Tag repository
        
    Returns:
        List of tags
    """
    tags = await repo.get_all(skip=skip, limit=limit)
    return [TagResponse.from_orm(tag) for tag in tags]


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: str,
    repo: TagRepository = Depends(get_tag_repo),
) -> TagResponse:
    """Get specific tag by ID.
    
    Args:
        tag_id: Tag ID
        repo: Tag repository
        
    Returns:
        Tag details
        
    Raises:
        HTTPException: If tag not found
    """
    tag = await repo.get_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return TagResponse.from_orm(tag)


@router.post("/", response_model=TagResponse, status_code=201)
async def create_tag(
    request: CreateTagRequest,
    repo: TagRepository = Depends(get_tag_repo),
) -> TagResponse:
    """Create new tag.
    
    Args:
        request: Tag creation request
        repo: Tag repository
        
    Returns:
        Created tag
        
    Raises:
        HTTPException: If tag name already exists
    """
    # Check for duplicates
    existing = await repo.find_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail="Tag already exists")
    
    from src.models.media import Tag
    tag = Tag(name=request.name, description=request.description)
    
    created = await repo.create(tag)
    await repo.commit()
    
    return TagResponse.from_orm(created)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str,
    request: UpdateTagRequest,
    repo: TagRepository = Depends(get_tag_repo),
) -> TagResponse:
    """Update tag.
    
    Args:
        tag_id: Tag ID
        request: Update request
        repo: Tag repository
        
    Returns:
        Updated tag
        
    Raises:
        HTTPException: If tag not found
    """
    tag = await repo.get_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if request.name:
        tag.name = request.name
    if request.description is not None:
        tag.description = request.description
    
    updated = await repo.update(tag)
    await repo.commit()
    
    return TagResponse.from_orm(updated)


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    repo: TagRepository = Depends(get_tag_repo),
) -> None:
    """Delete tag.
    
    Args:
        tag_id: Tag ID
        repo: Tag repository
        
    Raises:
        HTTPException: If tag not found
    """
    deleted = await repo.delete(tag_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    await repo.commit()


@router.get("/popular/", response_model=List[TagResponse])
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    repo: TagRepository = Depends(get_tag_repo),
) -> List[TagResponse]:
    """Get most popular tags.
    
    Args:
        limit: Number of tags to return
        repo: Tag repository
        
    Returns:
        List of popular tags
    """
    tags = await repo.get_popular(limit=limit)
    return [TagResponse.from_orm(tag) for tag in tags]


@router.get("/unused/", response_model=List[TagResponse])
async def get_unused_tags(
    repo: TagRepository = Depends(get_tag_repo),
) -> List[TagResponse]:
    """Get unused tags (not assigned to any media).
    
    Args:
        repo: Tag repository
        
    Returns:
        List of unused tags
    """
    tags = await repo.get_unused()
    return [TagResponse.from_orm(tag) for tag in tags]


@router.delete("/unused/all", status_code=204)
async def delete_unused_tags(
    repo: TagRepository = Depends(get_tag_repo),
) -> None:
    """Delete all unused tags.
    
    Args:
        repo: Tag repository
    """
    await repo.delete_unused()
    await repo.commit()
