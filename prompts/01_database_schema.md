# Prompt 01: Database Schema Implementation

## Metadata
- **Phase**: Foundation
- **Priority**: Critical
- **Estimated Time**: 2-3 hours
- **Dependencies**: None
- **Files to Create**: `src/models/base.py`, `src/models/media.py`, `src/models/metadata.py`, `src/core/database.py`

---

# GITHUB COPILOT PROMPT: DATABASE SCHEMA IMPLEMENTATION

## Context

You are implementing the complete database schema for MediaForge, a comprehensive media library management system. The database must efficiently store and query millions of media files with rich metadata, support full-text search, handle relationships between media items, and enable fast filtering and sorting operations.

## Project Structure

MediaForge uses:
- **Python 3.11+** with type hints
- **SQLAlchemy 2.0** for ORM
- **SQLite** as the database engine
- **Alembic** for migrations
- **Pydantic** for data validation

## Technical Requirements

### Database Architecture

1. **Base Model**: Create an abstract base model with common fields
2. **Media Items**: Primary table storing all media files
3. **Metadata**: Flexible metadata storage supporting multiple formats
4. **Tags**: Many-to-many relationship for categorization
5. **Collections**: Logical grouping of media items
6. **Indexes**: Optimized for common query patterns

### Required Tables

#### 1. MediaItem (Primary Table)
```python
class MediaItem:
    # Primary Key
    id: UUID (primary key, default=uuid4)
    
    # File Information
    file_path: str (unique, indexed, not null)
    file_name: str (indexed, not null)
    file_size: int (not null)
    file_hash: str (unique, indexed, not null)  # SHA256 for deduplication
    mime_type: str (indexed, not null)
    
    # Media Type Classification
    media_type: Enum("video", "audio", "image", "document", "other") (indexed)
    
    # Timestamps
    created_at: datetime (default=utcnow, indexed)
    modified_at: datetime (default=utcnow, onupdate=utcnow)
    file_created_at: datetime (nullable)
    file_modified_at: datetime (nullable)
    last_scanned_at: datetime (nullable)
    
    # Processing Status
    is_processed: bool (default=False, indexed)
    is_compressed: bool (default=False)
    compression_ratio: float (nullable)
    
    # Relationships
    metadata: relationship("MediaMetadata", back_populates="media_item", cascade="all, delete-orphan")
    tags: relationship("Tag", secondary="media_tags", back_populates="media_items")
    collections: relationship("Collection", secondary="collection_items", back_populates="media_items")
```

#### 2. MediaMetadata (Flexible Metadata Storage)
```python
class MediaMetadata:
    id: UUID (primary key)
    media_item_id: UUID (foreign key to MediaItem, not null, indexed)
    
    # Video Metadata
    duration: float (nullable)  # seconds
    width: int (nullable)
    height: int (nullable)
    fps: float (nullable)
    video_codec: str (nullable)
    audio_codec: str (nullable)
    bitrate: int (nullable)
    
    # Audio Metadata
    sample_rate: int (nullable)
    channels: int (nullable)
    artist: str (nullable, indexed)
    album: str (nullable, indexed)
    title: str (nullable, indexed)
    year: int (nullable)
    genre: str (nullable, indexed)
    
    # Image Metadata
    camera_make: str (nullable)
    camera_model: str (nullable)
    iso: int (nullable)
    aperture: float (nullable)
    shutter_speed: str (nullable)
    focal_length: float (nullable)
    
    # Geolocation
    latitude: float (nullable)
    longitude: float (nullable)
    location_name: str (nullable)
    
    # Additional Metadata (JSON field for extensibility)
    extra_metadata: JSON (default={})
    
    # Relationships
    media_item: relationship("MediaItem", back_populates="metadata")
```

#### 3. Tag (Many-to-Many)
```python
class Tag:
    id: UUID (primary key)
    name: str (unique, indexed, not null)
    description: str (nullable)
    color: str (nullable)  # Hex color for UI
    created_at: datetime (default=utcnow)
    
    # Relationships
    media_items: relationship("MediaItem", secondary="media_tags", back_populates="tags")
```

#### 4. Collection (Logical Grouping)
```python
class Collection:
    id: UUID (primary key)
    name: str (unique, indexed, not null)
    description: str (nullable)
    created_at: datetime (default=utcnow)
    modified_at: datetime (default=utcnow, onupdate=utcnow)
    
    # Relationships
    media_items: relationship("MediaItem", secondary="collection_items", back_populates="collections")
```

#### 5. Association Tables
```python
media_tags = Table(
    "media_tags",
    Column("media_item_id", UUID, ForeignKey("media_items.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow)
)

collection_items = Table(
    "collection_items",
    Column("collection_id", UUID, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    Column("media_item_id", UUID, ForeignKey("media_items.id", ondelete="CASCADE"), primary_key=True),
    Column("position", Integer, nullable=True),  # For ordered collections
    Column("added_at", DateTime, default=datetime.utcnow)
)
```

### Required Indexes

Create indexes for:
1. `file_path` (unique)
2. `file_hash` (unique, for deduplication)
3. `media_type` (for filtering)
4. `created_at` (for sorting)
5. `is_processed` (for processing queue)
6. `mime_type` (for type-based queries)
7. `artist`, `album`, `title`, `genre` (for audio library)
8. Composite index on `(media_type, created_at)` for common queries

## Implementation Instructions

### Step 1: Create Base Model (`src/models/base.py`)

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime
from datetime import datetime
from uuid import UUID, uuid4
from typing import Any

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

class TimestampMixin:
    """Mixin for created_at and modified_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    modified_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

class UUIDMixin:
    """Mixin for UUID primary key"""
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
```

Implement this with proper type hints and docstrings.

### Step 2: Create Media Models (`src/models/media.py`)

Implement all models listed above with:
- Complete SQLAlchemy 2.0 syntax
- Proper type hints using `Mapped[]`
- Comprehensive docstrings
- All relationships defined
- Proper cascade behaviors

### Step 3: Create Database Engine (`src/core/database.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class Database:
    def __init__(self, database_url: str):
        # Create async engine
        # Configure connection pool
        # Set up session maker
        pass
    
    async def create_tables(self) -> None:
        """Create all database tables"""
        pass
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution)"""
        pass
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope for database operations"""
        pass
```

Implement with:
- Async/await support
- Connection pooling
- Transaction management
- Error handling

### Step 4: Create Alembic Migration

Generate initial migration:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
```

## Testing Requirements

Create `tests/unit/test_models.py` with:

1. **Test Model Creation**
   - Create instances of each model
   - Validate all fields
   - Test default values

2. **Test Relationships**
   - MediaItem ↔ MediaMetadata (one-to-one)
   - MediaItem ↔ Tag (many-to-many)
   - MediaItem ↔ Collection (many-to-many)

3. **Test Constraints**
   - Unique constraints (file_path, file_hash)
   - Foreign key constraints
   - Not null constraints

4. **Test Indexes**
   - Verify indexes are created
   - Test query performance

5. **Test CRUD Operations**
   - Create, Read, Update, Delete for all models
   - Test cascade deletes
   - Test bulk operations

## Success Criteria

- [ ] All models defined with complete type hints
- [ ] All relationships properly configured
- [ ] Database engine with async support
- [ ] All indexes created
- [ ] Alembic migration generated
- [ ] Unit tests pass (100% coverage for models)
- [ ] No mypy errors
- [ ] No flake8 warnings
- [ ] Docstrings complete for all classes and methods

## Code Quality Standards

- Use SQLAlchemy 2.0 syntax (Mapped[], mapped_column())
- Include comprehensive docstrings (Google style)
- Add type hints for all function parameters and returns
- Follow Python naming conventions (snake_case)
- Add comments for complex logic
- Use enums for fixed value sets
- Implement proper error handling

## Example Usage Pattern

The implementation should support this usage pattern:

```python
from src.core.database import Database
from src.models.media import MediaItem, MediaMetadata

# Initialize database
db = Database("sqlite+aiosqlite:///data/mediaforge.db")
await db.create_tables()

# Create media item
async with db.session() as session:
    media_item = MediaItem(
        file_path="/media/video.mp4",
        file_name="video.mp4",
        file_size=1024000,
        file_hash="abc123...",
        mime_type="video/mp4",
        media_type="video"
    )
    session.add(media_item)
    await session.commit()
```

## Notes for Copilot

- Focus on creating a robust, scalable schema
- Prioritize query performance
- Support millions of media items
- Enable efficient filtering and sorting
- Allow for future extensibility
- Use JSON fields for flexible metadata
- Implement proper cascade behaviors
- Create comprehensive indexes

---

**GENERATE COMPLETE, PRODUCTION-READY CODE FOR ALL REQUIREMENTS ABOVE**