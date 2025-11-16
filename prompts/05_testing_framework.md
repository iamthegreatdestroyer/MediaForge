# Prompt 05: Testing Framework Setup

## Metadata
- **Phase**: Foundation
- **Priority**: High
- **Estimated Time**: 2-3 hours
- **Dependencies**: Prompts 01-04
- **Files to Create**: Test infrastructure and fixtures

---

# GITHUB COPILOT PROMPT: TESTING FRAMEWORK IMPLEMENTATION

## Context

You are setting up a comprehensive testing framework for MediaForge using pytest. The framework must support:
- Unit tests for all modules
- Integration tests for workflows
- Async test support
- Database fixtures
- Sample media file fixtures
- Code coverage reporting
- Performance benchmarking

## Technical Requirements

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_scanner.py
│   ├── test_metadata.py
│   ├── test_hasher.py
│   └── test_cli.py
├── integration/         # Integration tests
│   ├── test_scan_workflow.py
│   └── test_metadata_workflow.py
├── performance/         # Performance benchmarks
│   └── test_scan_performance.py
├── fixtures/            # Test data
│   ├── sample_video.mp4
│   ├── sample_audio.mp3
│   └── sample_image.jpg
└── conftest.py         # Shared fixtures
```

### Enhanced conftest.py

```python
import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Database
from src.models.media import MediaItem, Tag, Collection
from src.core.config import Settings

# Test Settings
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing"""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        media_root=Path("/tmp/test_media"),
        cache_dir=Path("/tmp/test_cache"),
        debug=True
    )

# Database Fixtures
@pytest_asyncio.fixture(scope="function")
async def db(test_settings) -> AsyncGenerator[Database, None]:
    """Provide a clean database for each test"""
    database = Database(test_settings.database_url)
    await database.create_tables()
    yield database
    await database.drop_tables()

@pytest_asyncio.fixture
async def db_session(db: Database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session"""
    async with db.session() as session:
        yield session

# File System Fixtures
@pytest.fixture
def temp_media_dir(tmp_path) -> Path:
    """Create temporary media directory"""
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    return media_dir

@pytest.fixture
def sample_video_file(temp_media_dir) -> Path:
    """Create a minimal test video file"""
    import ffmpeg
    
    video_path = temp_media_dir / "test_video.mp4"
    
    # Generate a 5-second test video
    (
        ffmpeg
        .input('color=c=blue:s=1920x1080:d=5', f='lavfi')
        .output(str(video_path), vcodec='libx264', pix_fmt='yuv420p')
        .overwrite_output()
        .run(quiet=True)
    )
    
    return video_path

@pytest.fixture
def sample_audio_file(temp_media_dir) -> Path:
    """Create a minimal test audio file"""
    import ffmpeg
    
    audio_path = temp_media_dir / "test_audio.mp3"
    
    # Generate a 5-second test audio
    (
        ffmpeg
        .input('sine=frequency=1000:duration=5', f='lavfi')
        .output(str(audio_path), acodec='libmp3lame')
        .overwrite_output()
        .run(quiet=True)
    )
    
    return audio_path

@pytest.fixture
def sample_image_file(temp_media_dir) -> Path:
    """Create a test image file"""
    from PIL import Image, ImageDraw
    
    image_path = temp_media_dir / "test_image.jpg"
    
    # Create a simple test image
    img = Image.new('RGB', (1920, 1080), color='blue')
    draw = ImageDraw.Draw(img)
    draw.text((960, 540), "Test Image", fill='white')
    img.save(image_path, 'JPEG')
    
    return image_path

# Database Data Fixtures
@pytest_asyncio.fixture
async def sample_media_item(db_session: AsyncSession, sample_video_file: Path) -> MediaItem:
    """Create a sample media item in database"""
    media_item = MediaItem(
        file_path=str(sample_video_file),
        file_name=sample_video_file.name,
        file_size=sample_video_file.stat().st_size,
        file_hash="test_hash_123",
        mime_type="video/mp4",
        media_type="video"
    )
    db_session.add(media_item)
    await db_session.commit()
    await db_session.refresh(media_item)
    return media_item

@pytest_asyncio.fixture
async def sample_tags(db_session: AsyncSession) -> list[Tag]:
    """Create sample tags"""
    tags = [
        Tag(name="vacation", description="Vacation media", color="#3498db"),
        Tag(name="family", description="Family content", color="#e74c3c"),
        Tag(name="work", description="Work-related", color="#2ecc71")
    ]
    for tag in tags:
        db_session.add(tag)
    await db_session.commit()
    return tags

@pytest_asyncio.fixture
async def sample_collection(db_session: AsyncSession) -> Collection:
    """Create sample collection"""
    collection = Collection(
        name="Test Collection",
        description="A test collection"
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)
    return collection

# Utility Fixtures
@pytest.fixture
def mock_progress_callback():
    """Mock progress callback for testing"""
    def callback(current: int, total: int):
        pass
    return callback
```

### Example Unit Tests

Create `tests/unit/test_models.py`:

```python
import pytest
from datetime import datetime
from src.models.media import MediaItem, MediaMetadata, Tag

@pytest.mark.asyncio
async def test_create_media_item(db_session):
    """Test creating a media item"""
    media_item = MediaItem(
        file_path="/test/path.mp4",
        file_name="path.mp4",
        file_size=1024000,
        file_hash="abc123",
        mime_type="video/mp4",
        media_type="video"
    )
    
    db_session.add(media_item)
    await db_session.commit()
    
    assert media_item.id is not None
    assert media_item.created_at is not None

@pytest.mark.asyncio
async def test_media_item_relationships(db_session, sample_media_item, sample_tags):
    """Test media item relationships"""
    # Add tags to media item
    sample_media_item.tags.extend(sample_tags)
    await db_session.commit()
    
    # Verify relationship
    await db_session.refresh(sample_media_item)
    assert len(sample_media_item.tags) == len(sample_tags)

# Add more tests...
```

### Integration Tests

Create `tests/integration/test_scan_workflow.py`:

```python
import pytest
from pathlib import Path
from src.core.scanner import MediaScanner
from src.core.database import Database

@pytest.mark.asyncio
async def test_full_scan_workflow(
    db,
    temp_media_dir,
    sample_video_file,
    sample_audio_file,
    sample_image_file
):
    """Test complete scanning workflow"""
    scanner = MediaScanner(db)
    
    # Perform scan
    result = await scanner.scan_directory(
        temp_media_dir,
        recursive=True,
        incremental=False
    )
    
    # Verify results
    assert result.total_files == 3
    assert result.new_files == 3
    assert result.error_files == 0
    
    # Verify database entries
    async with db.session() as session:
        from sqlalchemy import select
        from src.models.media import MediaItem
        
        items = await session.execute(select(MediaItem))
        all_items = items.scalars().all()
        
        assert len(all_items) == 3
```

## Testing Commands

Add to project documentation:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run with verbose output
pytest -v

# Run only async tests
pytest -m asyncio

# Run performance tests
pytest tests/performance/
```

## Success Criteria

- [ ] All test fixtures work
- [ ] Sample media files generate
- [ ] Database fixtures functional
- [ ] Tests can run in isolation
- [ ] Coverage reporting works
- [ ] Async tests execute properly

---

**GENERATE COMPLETE, PRODUCTION-READY CODE FOR ALL REQUIREMENTS ABOVE**