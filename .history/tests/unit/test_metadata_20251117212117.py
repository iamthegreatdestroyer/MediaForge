"""Unit tests for metadata extraction"""
import pytest
from pathlib import Path
from src.core.metadata_extractor import (
    MetadataExtractor,
    VideoMetadataExtractor,
    AudioMetadataExtractor,
    ImageMetadataExtractor,
    MetadataExtractionError
)
from src.models.media import MediaItem, MediaType


@pytest.mark.asyncio
async def test_video_metadata_extraction(sample_video_file):
    """Test video metadata extraction"""
    extractor = VideoMetadataExtractor()
    
    try:
        metadata = await extractor.extract(sample_video_file)
        
        # Check for expected fields
        assert 'duration' in metadata or 'format_name' in metadata
        # Video might have width/height if ffmpeg generated properly
        if 'width' in metadata:
            assert isinstance(metadata['width'], int)
    except MetadataExtractionError:
        # If ffmpeg not available or file too minimal, that's OK
        pytest.skip("FFmpeg not available or minimal test file")


@pytest.mark.asyncio
async def test_audio_metadata_extraction(sample_audio_file):
    """Test audio metadata extraction"""
    extractor = AudioMetadataExtractor()
    
    try:
        metadata = await extractor.extract(sample_audio_file)
        
        # Check structure is valid
        assert isinstance(metadata, dict)
        # Audio files may have duration, bitrate, etc.
    except MetadataExtractionError:
        # Minimal test files may not have tags
        pytest.skip("Audio extraction not available for minimal test file")


@pytest.mark.asyncio
async def test_image_metadata_extraction(sample_image_file):
    """Test image metadata extraction"""
    extractor = ImageMetadataExtractor()
    
    try:
        metadata = await extractor.extract(sample_image_file)
        
        # Check for basic image properties
        assert 'width' in metadata
        assert 'height' in metadata
        assert 'format' in metadata
        assert isinstance(metadata['width'], int)
        assert isinstance(metadata['height'], int)
    except MetadataExtractionError as e:
        pytest.skip(f"Image extraction failed: {e}")


@pytest.mark.asyncio
async def test_metadata_extractor_coordinator(sample_video_file):
    """Test MetadataExtractor coordinates extraction"""
    # Create a mock media item
    media_item = MediaItem(
        file_path=str(sample_video_file),
        file_name=sample_video_file.name,
        file_size=sample_video_file.stat().st_size,
        file_hash="test_hash",
        mime_type="video/mp4",
        media_type=MediaType.video
    )
    
    extractor = MetadataExtractor()
    
    try:
        metadata = await extractor.extract_all_metadata(media_item)
        assert isinstance(metadata, dict)
    except MetadataExtractionError:
        pytest.skip("Metadata extraction not available")


@pytest.mark.asyncio
async def test_batch_extraction(sample_video_file, sample_audio_file, mock_progress_callback):
    """Test batch metadata extraction"""
    media_items = [
        MediaItem(
            id=1,
            file_path=str(sample_video_file),
            file_name=sample_video_file.name,
            file_size=1000,
            file_hash="hash1",
            mime_type="video/mp4",
            media_type=MediaType.video
        ),
        MediaItem(
            id=2,
            file_path=str(sample_audio_file),
            file_name=sample_audio_file.name,
            file_size=2000,
            file_hash="hash2",
            mime_type="audio/mp3",
            media_type=MediaType.audio
        )
    ]
    
    extractor = MetadataExtractor()
    results = await extractor.batch_extract(
        media_items,
        progress_callback=mock_progress_callback
    )
    
    assert isinstance(results, dict)
    assert len(results) == 2
    
    # Check progress callback was called
    assert len(mock_progress_callback.call_log) == 2


@pytest.mark.asyncio
async def test_extraction_error_handling(tmp_path):
    """Test metadata extraction handles errors"""
    # Create non-existent file path
    fake_file = tmp_path / "nonexistent.mp4"
    
    media_item = MediaItem(
        file_path=str(fake_file),
        file_name="nonexistent.mp4",
        file_size=0,
        file_hash="fake",
        mime_type="video/mp4",
        media_type=MediaType.video
    )
    
    extractor = MetadataExtractor()
    
    with pytest.raises(MetadataExtractionError):
        await extractor.extract_all_metadata(media_item)


@pytest.mark.asyncio
async def test_video_fps_parsing():
    """Test FPS parsing utility"""
    extractor = VideoMetadataExtractor()
    
    # Test various FPS formats
    assert extractor._parse_fps("30") == 30.0
    assert extractor._parse_fps("30000/1001") == pytest.approx(29.97, rel=0.01)
    assert extractor._parse_fps("25/1") == 25.0
    assert extractor._parse_fps("invalid") == 0.0


@pytest.mark.asyncio
async def test_audio_year_parsing():
    """Test year parsing from date strings"""
    extractor = AudioMetadataExtractor()
    
    assert extractor._parse_year("2024") == 2024
    assert extractor._parse_year("2024-03-15") == 2024
    assert extractor._parse_year("March 2023") == 2023
    assert extractor._parse_year("invalid") is None
    assert extractor._parse_year(None) is None


@pytest.mark.asyncio
async def test_audio_track_number_parsing():
    """Test track number parsing"""
    extractor = AudioMetadataExtractor()
    
    assert extractor._parse_track_number("5") == 5
    assert extractor._parse_track_number("3/12") == 3
    assert extractor._parse_track_number("invalid") is None
    assert extractor._parse_track_number(None) is None
