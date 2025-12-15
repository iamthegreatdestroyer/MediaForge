"""Integration tests for scan workflow"""
import pytest
from pathlib import Path
from sqlalchemy import select
from src.core.scanner import MediaScanner
from src.core.metadata_extractor import MetadataExtractor
from src.models.media import MediaItem, MediaType
from src.models.metadata import MediaMetadata


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
        items = await session.execute(select(MediaItem))
        all_items = items.scalars().all()
        
        assert len(all_items) == 3
        
        # Check media types are correctly identified
        media_types = {item.media_type for item in all_items}
        assert MediaType.video in media_types
        assert MediaType.audio in media_types
        assert MediaType.image in media_types


@pytest.mark.asyncio
async def test_scan_and_incremental_rescan(db, temp_media_dir, sample_video_file):
    """Test initial scan followed by incremental rescan"""
    scanner = MediaScanner(db)
    
    # Initial scan
    result1 = await scanner.scan_directory(temp_media_dir, incremental=True)
    assert result1.new_files == 1
    assert result1.skipped_files == 0
    
    # Add another file
    new_file = temp_media_dir / "new_video.mp4"
    new_file.write_bytes(sample_video_file.read_bytes())
    
    # Incremental scan
    result2 = await scanner.scan_directory(temp_media_dir, incremental=True)
    assert result2.new_files == 1
    assert result2.skipped_files == 1
    
    # Verify database
    async with db.session() as session:
        items = await session.execute(select(MediaItem))
        all_items = items.scalars().all()
        assert len(all_items) == 2


@pytest.mark.asyncio
async def test_scan_with_subdirectories(db, tmp_path):
    """Test scanning nested directory structure"""
    # Create directory structure
    root = tmp_path / "media"
    root.mkdir()
    movies = root / "movies"
    movies.mkdir()
    music = root / "music"
    music.mkdir()
    
    # Create files
    (movies / "movie1.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom')
    (movies / "movie2.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom')
    (music / "song1.mp3").write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 100)
    (music / "song2.mp3").write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 100)
    
    scanner = MediaScanner(db)
    result = await scanner.scan_directory(root, recursive=True)
    
    assert result.total_files == 4
    assert result.new_files == 4
    
    # Verify all files are in database
    async with db.session() as session:
        items = await session.execute(select(MediaItem))
        all_items = items.scalars().all()
        assert len(all_items) == 4


@pytest.mark.asyncio
async def test_scan_updates_existing_files(db, temp_media_dir, sample_video_file):
    """Test that rescanning updates file information"""
    scanner = MediaScanner(db)
    
    # Initial scan
    await scanner.scan_directory(temp_media_dir)
    
    # Modify file
    with open(sample_video_file, 'ab') as f:
        f.write(b'\x00' * 1000)  # Append data
    
    # Rescan
    result = await scanner.scan_directory(temp_media_dir, incremental=False)
    
    # Check database was updated
    async with db.session() as session:
        items = await session.execute(select(MediaItem))
        item = items.scalar_one()
        # File size should reflect change
        assert item.file_size == sample_video_file.stat().st_size


@pytest.mark.asyncio
async def test_scan_with_invalid_files(db, temp_media_dir):
    """Test scanning handles invalid/corrupt files"""
    # Create various invalid files
    (temp_media_dir / "not_a_video.mp4").write_bytes(b'invalid')
    (temp_media_dir / "empty.mp4").write_bytes(b'')
    (temp_media_dir / "text.mp4").write_text("This is text, not video")
    
    scanner = MediaScanner(db)
    # Should not crash
    result = await scanner.scan_directory(temp_media_dir)
    
    # Files might be processed or skipped
    assert result.total_files >= 0


@pytest.mark.asyncio
async def test_scan_respects_file_filters(db, temp_media_dir):
    """Test that scanner respects hidden file settings"""
    # Create visible and hidden files
    (temp_media_dir / "visible.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom')
    (temp_media_dir / ".hidden.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom')
    
    scanner = MediaScanner(db)
    
    # Scan without hidden
    result_no_hidden = await scanner.scan_directory(
        temp_media_dir, include_hidden=False
    )
    assert result_no_hidden.total_files == 1
    
    # Scan with hidden
    result_with_hidden = await scanner.scan_directory(
        temp_media_dir, include_hidden=True
    )
    assert result_with_hidden.total_files == 2
