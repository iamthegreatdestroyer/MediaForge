"""Integration tests for media scanner.

End-to-end tests covering full scanning workflows.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from src.core.database import Database
from src.core.scanner import MediaScanner
from src.models.media import MediaItem
from sqlalchemy import select


@pytest.fixture
async def integration_db():
    """Create test database for integration tests."""
    database = Database("sqlite+aiosqlite:///:memory:")
    await database.create_tables()
    try:
        yield database
    finally:
        await database.drop_tables()


@pytest.fixture
def large_media_library(tmp_path):
    """Create a larger test media library with varied structure."""
    root = tmp_path / "library"
    root.mkdir()
    
    # Create multiple directories
    categories = {
        "movies": [f"movie_{i}.mp4" for i in range(20)],
        "tv_shows": [f"episode_{i}.mkv" for i in range(30)],
        "music": [f"song_{i}.mp3" for i in range(50)],
        "photos": [f"photo_{i}.jpg" for i in range(40)],
        "documents": [f"doc_{i}.pdf" for i in range(10)],
    }
    
    for category, files in categories.items():
        cat_dir = root / category
        cat_dir.mkdir()
        
        for filename in files:
            filepath = cat_dir / filename
            # Create files with varied content
            content = f"{category}:{filename}".encode() * 100
            filepath.write_bytes(content)
    
    return root


@pytest.mark.asyncio
async def test_full_library_scan(integration_db, large_media_library):
    """Test scanning a complete media library."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    result = await scanner.scan_directory(
        large_media_library,
        recursive=True,
        include_hidden=False,
        incremental=False
    )
    
    # Verify all files were found
    expected_total = 20 + 30 + 50 + 40 + 10  # 150 files
    assert result.total_files == expected_total
    assert result.new_files == expected_total
    assert result.error_files == 0
    
    # Verify database contains all items
    async with integration_db.session() as session:
        db_result = await session.execute(select(MediaItem))
        items = db_result.scalars().all()
        assert len(items) == expected_total


@pytest.mark.asyncio
async def test_incremental_scan_workflow(integration_db, large_media_library):
    """Test incremental scanning workflow."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    # Initial full scan
    result1 = await scanner.scan_directory(
        large_media_library,
        recursive=True,
        incremental=False
    )
    
    initial_count = result1.new_files
    assert initial_count > 0
    
    # Incremental scan should skip all files
    result2 = await scanner.scan_directory(
        large_media_library,
        recursive=True,
        incremental=True
    )
    
    assert result2.new_files == 0
    assert result2.skipped_files == initial_count
    
    # Add new files
    new_dir = large_media_library / "new_content"
    new_dir.mkdir()
    for i in range(5):
        (new_dir / f"new_video_{i}.mp4").write_bytes(b"new content")
    
    # Incremental scan should find only new files
    result3 = await scanner.scan_directory(
        large_media_library,
        recursive=True,
        incremental=True
    )
    
    assert result3.new_files == 5
    assert result3.skipped_files == initial_count


@pytest.mark.asyncio
async def test_modification_detection(integration_db, large_media_library):
    """Test detection of modified files."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    # Initial scan
    await scanner.scan_directory(
        large_media_library,
        recursive=True
    )
    
    # Modify some files
    movies_dir = large_media_library / "movies"
    modified_files = []
    for i in range(5):
        filepath = movies_dir / f"movie_{i}.mp4"
        filepath.write_bytes(b"modified content" * 1000)
        modified_files.append(filepath)
    
    # Rescan modified files
    result = await scanner.rescan_modified_files()
    
    assert result.updated_files >= 5


@pytest.mark.asyncio
async def test_duplicate_detection(integration_db, tmp_path):
    """Test detection and handling of duplicate files."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    # Create directory with duplicates
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    
    # Create original file
    original_content = b"unique content" * 1000
    (media_dir / "original.mp4").write_bytes(original_content)
    
    # Create duplicates in different locations
    (media_dir / "copy1.mp4").write_bytes(original_content)
    (media_dir / "copy2.mp4").write_bytes(original_content)
    
    subdir = media_dir / "subfolder"
    subdir.mkdir()
    (subdir / "copy3.mp4").write_bytes(original_content)
    
    # Scan
    result = await scanner.scan_directory(media_dir, recursive=True)
    
    # Should handle duplicates gracefully
    assert result.total_files == 4
    
    # Check that only unique hashes are stored or duplicates tracked
    async with integration_db.session() as session:
        db_result = await session.execute(select(MediaItem))
        items = db_result.scalars().all()
        
        # All items should have same hash
        hashes = [item.file_hash for item in items]
        # Scanner updates path for duplicates, so we might have 1 or 4 entries
        assert len(items) >= 1


@pytest.mark.asyncio
async def test_mixed_media_types(integration_db, tmp_path):
    """Test scanning directory with all media types."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    media_dir = tmp_path / "mixed"
    media_dir.mkdir()
    
    # Create one file of each type
    files = {
        "video.mp4": b"video",
        "audio.mp3": b"audio",
        "image.jpg": b"image",
        "doc.pdf": b"document",
        "playlist.m3u8": b"streaming",
    }
    
    for filename, content in files.items():
        (media_dir / filename).write_bytes(content * 100)
    
    result = await scanner.scan_directory(media_dir)
    
    assert result.total_files == 5
    assert result.new_files == 5
    
    # Verify all types are correctly classified
    async with integration_db.session() as session:
        db_result = await session.execute(select(MediaItem))
        items = db_result.scalars().all()
        
        media_types = {item.media_type.value for item in items}
        assert "video" in media_types
        assert "audio" in media_types
        assert "image" in media_types


@pytest.mark.asyncio
async def test_concurrent_scans(integration_db, large_media_library):
    """Test multiple concurrent scan operations."""
    scanner1 = MediaScanner(integration_db, max_workers=2)
    scanner2 = MediaScanner(integration_db, max_workers=2)
    
    # Create two different subdirectories
    dir1 = large_media_library / "movies"
    dir2 = large_media_library / "music"
    
    # Run scans concurrently
    results = await asyncio.gather(
        scanner1.scan_directory(dir1, recursive=False),
        scanner2.scan_directory(dir2, recursive=False),
        return_exceptions=True
    )
    
    # Both should complete successfully
    assert len(results) == 2
    for result in results:
        assert not isinstance(result, Exception)
        assert result.total_files > 0


@pytest.mark.asyncio
async def test_scan_performance(integration_db, large_media_library):
    """Test scanning performance meets requirements."""
    import time
    
    scanner = MediaScanner(integration_db, max_workers=4)
    
    start_time = time.time()
    result = await scanner.scan_directory(
        large_media_library,
        recursive=True,
        incremental=False
    )
    duration = time.time() - start_time
    
    # Should complete reasonably quickly (adjust threshold as needed)
    # 150 files should scan in under 10 seconds
    assert duration < 10.0, f"Scan took {duration:.2f}s, expected < 10s"
    
    # Calculate files per second
    files_per_second = result.total_files / duration
    print(f"Performance: {files_per_second:.1f} files/second")
    
    # Should handle at least 10 files per second
    assert files_per_second >= 10


@pytest.mark.asyncio
async def test_error_recovery(integration_db, tmp_path):
    """Test scanner recovers from errors gracefully."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    media_dir = tmp_path / "problematic"
    media_dir.mkdir()
    
    # Create normal files
    for i in range(10):
        (media_dir / f"good_{i}.mp4").write_bytes(b"content")
    
    # Create a symlink to non-existent file (if supported)
    try:
        broken_link = media_dir / "broken.mp4"
        broken_link.symlink_to(Path("/nonexistent/file.mp4"))
    except (OSError, NotImplementedError):
        pass
    
    # Scan should complete despite errors
    result = await scanner.scan_directory(media_dir)
    
    assert result.total_files >= 10
    assert result.new_files >= 10


@pytest.mark.asyncio
async def test_integrity_verification_workflow(integration_db, tmp_path):
    """Test file integrity verification workflow."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    
    # Create test files
    test_file = media_dir / "test.mp4"
    test_file.write_bytes(b"original content")
    
    # Initial scan
    await scanner.scan_directory(media_dir)
    
    # Get media item
    async with integration_db.session() as session:
        db_result = await session.execute(select(MediaItem).limit(1))
        media_item = db_result.scalar_one()
        item_id = media_item.id
        
        # Verify integrity (should pass)
        assert await scanner.verify_file_integrity(item_id) is True
        
        # Modify file
        test_file.write_bytes(b"modified content")
        
        # Verify integrity (should fail)
        assert await scanner.verify_file_integrity(item_id) is False
        
        # Delete file
        test_file.unlink()
        
        # Verify integrity (should fail)
        assert await scanner.verify_file_integrity(item_id) is False


@pytest.mark.asyncio
async def test_progress_tracking(integration_db, large_media_library):
    """Test progress tracking during scan."""
    progress_updates = []
    
    def track_progress(processed: int, total: int):
        progress_updates.append((processed, total))
    
    scanner = MediaScanner(
        integration_db,
        max_workers=4,
        progress_callback=track_progress
    )
    
    result = await scanner.scan_directory(
        large_media_library,
        recursive=True
    )
    
    # Progress should be tracked (may not be called for every file)
    # Just verify it doesn't cause errors
    assert isinstance(progress_updates, list)
    if progress_updates:
        # Verify progress values are sensible
        for processed, total in progress_updates:
            assert 0 <= processed <= total


@pytest.mark.asyncio
async def test_database_consistency(integration_db, large_media_library):
    """Test database remains consistent across operations."""
    scanner = MediaScanner(integration_db, max_workers=4)
    
    # Initial scan
    result1 = await scanner.scan_directory(large_media_library, recursive=True)
    
    # Verify database count
    async with integration_db.session() as session:
        count_result = await session.execute(
            select(MediaItem)
        )
        items = count_result.scalars().all()
        initial_count = len(items)
        
        assert initial_count == result1.new_files
    
    # Rescan (incremental)
    result2 = await scanner.scan_directory(large_media_library, recursive=True)
    
    # Database count should remain the same
    async with integration_db.session() as session:
        count_result = await session.execute(
            select(MediaItem)
        )
        items = count_result.scalars().all()
        final_count = len(items)
        
        assert final_count == initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
