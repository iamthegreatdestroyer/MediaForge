"""Collection endpoints router."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.schemas import CollectionResponse, CreateCollectionRequest, UpdateCollectionRequest
from src.api.app import get_db
from src.core.database import Database
from src.repositories.collection import CollectionRepository

router = APIRouter()


async def get_collection_repo(db: Database = Depends(get_db)) -> CollectionRepository:
    """Dependency: Get collection repository."""
    async with db.session() as session:
        yield CollectionRepository(session)


@router.get("/", response_model=List[CollectionResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    repo: CollectionRepository = Depends(get_collection_repo),
) -> List[CollectionResponse]:
    """Get paginated list of collections.
    
    Args:
        skip: Number of items to skip
        limit: Number of items to return
        repo: Collection repository
        
    Returns:
        List of collections
    """
    collections = await repo.get_all(skip=skip, limit=limit)
    return [CollectionResponse.from_orm(col) for col in collections]


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: str,
    repo: CollectionRepository = Depends(get_collection_repo),
) -> CollectionResponse:
    """Get specific collection by ID.
    
    Args:
        collection_id: Collection ID
        repo: Collection repository
        
    Returns:
        Collection details
        
    Raises:
        HTTPException: If collection not found
    """
    collection = await repo.get_by_id(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return CollectionResponse.from_orm(collection)


@router.post("/", response_model=CollectionResponse, status_code=201)
async def create_collection(
    request: CreateCollectionRequest,
    repo: CollectionRepository = Depends(get_collection_repo),
) -> CollectionResponse:
    """Create new collection.
    
    Args:
        request: Collection creation request
        repo: Collection repository
        
    Returns:
        Created collection
        
    Raises:
        HTTPException: If collection name already exists
    """
    # Check for duplicates
    existing = await repo.find_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail="Collection already exists")
    
    from src.models.media import Collection
    collection = Collection(name=request.name, description=request.description)
    
    created = await repo.create(collection)
    await repo.commit()
    
    return CollectionResponse.from_orm(created)


@router.patch("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    request: UpdateCollectionRequest,
    repo: CollectionRepository = Depends(get_collection_repo),
) -> CollectionResponse:
    """Update collection.
    
    Args:
        collection_id: Collection ID
        request: Update request
        repo: Collection repository
        
    Returns:
        Updated collection
        
    Raises:
        HTTPException: If collection not found
    """
    collection = await repo.get_by_id(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if request.name:
        collection.name = request.name
    if request.description is not None:
        collection.description = request.description
    
    updated = await repo.update(collection)
    await repo.commit()
    
    return CollectionResponse.from_orm(updated)


@router.delete("/{collection_id}", status_code=204)
async def delete_collection(
    collection_id: str,
    repo: CollectionRepository = Depends(get_collection_repo),
) -> None:
    """Delete collection.
    
    Args:
        collection_id: Collection ID
        repo: Collection repository
        
    Raises:
        HTTPException: If collection not found
    """
    deleted = await repo.delete(collection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    await repo.commit()


@router.get("/empty/", response_model=List[CollectionResponse])
async def get_empty_collections(
    repo: CollectionRepository = Depends(get_collection_repo),
) -> List[CollectionResponse]:
    """Get empty collections (with no media).
    
    Args:
        repo: Collection repository
        
    Returns:
        List of empty collections
    """
    collections = await repo.get_empty_collections()
    return [CollectionResponse.from_orm(col) for col in collections]


@router.delete("/empty/all", status_code=204)
async def delete_empty_collections(
    repo: CollectionRepository = Depends(get_collection_repo),
) -> None:
    """Delete all empty collections.
    
    Args:
        repo: Collection repository
    """
    await repo.delete_empty()
    await repo.commit()


@router.get("/stats/", response_model=List[dict])
async def get_collection_statistics(
    repo: CollectionRepository = Depends(get_collection_repo),
) -> List[dict]:
    """Get statistics about all collections.
    
    Args:
        repo: Collection repository
        
    Returns:
        List of collections with media counts
    """
    collections_with_counts = await repo.get_with_media_count()
    return [
        {
            "id": col.id,
            "name": col.name,
            "media_count": count,
        }
        for col, count in collections_with_counts
    ]
