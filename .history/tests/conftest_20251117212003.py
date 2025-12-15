"""Pytest configuration and fixtures"""
import pytest
import pytest_asyncio
from pathlib import Path
import tempfile
import shutil
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Database
from src.models.media import MediaItem, MediaType, Tag, Collection
from src.core.config import settings


# Test Settings
@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing"""
    class TestSettings:
        database_url = "sqlite+aiosqlite:///:memory:"
        media_root = Path("/tmp/test_media")
        cache_dir = Path("/tmp/test_cache")
        debug = True
    return TestSettings()


# Database Fixtures
@pytest_asyncio.fixture(scope="function")
async def db(test_settings) -> AsyncGenerator[Database, None]:
    """Provide a clean database for each test"""
    database = Database(test_settings.database_url)
    await database.create_tables()
    yield database
    # Cleanup
    try:
        await database.drop_tables()
    except Exception:
        pass


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
    import subprocess
    
    video_path = temp_media_dir / "test_video.mp4"
    
    # Generate a 5-second test video using ffmpeg CLI
    try:
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'color=c=blue:s=1920x1080:d=5',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-y', str(video_path)
        ], check=True, capture_output=True, timeout=30)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create a minimal MP4 file structure for testing
        # This is a valid minimal MP4 that parsers will accept
        video_path.write_bytes(
            b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41'
            b'\x00\x00\x00\x08free'
            b'\x00\x00\x00\x28mdat\x00\x00\x00\x00\x00\x00\x00\x00'
        )
    
    return video_path


@pytest.fixture
def sample_audio_file(temp_media_dir) -> Path:
    """Create a minimal test audio file"""
    import subprocess
    
    audio_path = temp_media_dir / "test_audio.mp3"
    
    # Generate a 5-second test audio using ffmpeg CLI
    try:
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=5',
            '-c:a', 'libmp3lame', '-y', str(audio_path)
        ], check=True, capture_output=True, timeout=30)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create a minimal MP3 file structure
        audio_path.write_bytes(
            b'\xff\xfb\x90\x00'  # MP3 sync word and header
            b'\x00' * 100  # Minimal frame data
        )
    
    return audio_path


@pytest.fixture
def sample_image_file(temp_media_dir) -> Path:
    """Create a test image file"""
    try:
        from PIL import Image, ImageDraw
        
        image_path = temp_media_dir / "test_image.jpg"
        
        # Create a simple test image
        img = Image.new('RGB', (1920, 1080), color='blue')
        draw = ImageDraw.Draw(img)
        draw.text((960, 540), "Test Image", fill='white')
        img.save(image_path, 'JPEG')
        
        return image_path
    except ImportError:
        # Fallback: create minimal JPEG structure
        image_path = temp_media_dir / "test_image.jpg"
        image_path.write_bytes(
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xd9'  # JPEG markers
        )
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
        media_type=MediaType.video
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
    # Refresh all tags to get IDs
    for tag in tags:
        await db_session.refresh(tag)
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
    call_log = []
    
    def callback(current: int, total: int):
        call_log.append((current, total))
    
    callback.call_log = call_log
    return callback
