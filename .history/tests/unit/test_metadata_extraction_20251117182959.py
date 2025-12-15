"""Unit tests for metadata extraction system.

Tests video, audio, and image metadata extraction plus thumbnail generation.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from src.core.metadata_extractor import (
    AudioMetadataExtractor,
    ImageMetadataExtractor,
    MetadataExtractor,
    MetadataExtractionError,
    VideoMetadataExtractor,
)
from src.core.thumbnail_generator import (
    ThumbnailGenerationError,
    ThumbnailGenerator,
)
from src.models.media import MediaItem, MediaType


# Test VideoMetadataExtractor

class TestVideoMetadataExtractor:
    """Tests for video metadata extraction."""
    
    @pytest.fixture
    def video_extractor(self):
        """Create video metadata extractor."""
        return VideoMetadataExtractor()
    
    @pytest.fixture
    def mock_video_probe(self):
        """Mock ffprobe output for video."""
        return {
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 1920,
                    'height': 1080,
                    'r_frame_rate': '30000/1001',
                },
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac',
                    'channels': 2,
                    'sample_rate': 48000,
                },
                {
                    'codec_type': 'subtitle',
                    'tags': {'language': 'eng'},
                },
            ],
            'format': {
                'duration': '120.5',
                'bit_rate': '5000000',
                'format_name': 'mp4',
            },
        }
    
    @pytest.mark.asyncio
    async def test_extract_video_metadata(self, video_extractor, mock_video_probe):
        """Test extracting video metadata."""
        with patch('ffmpeg.probe', return_value=mock_video_probe):
            metadata = await video_extractor.extract(Path('test.mp4'))
        
        assert metadata['duration'] == 120.5
        assert metadata['width'] == 1920
        assert metadata['height'] == 1080
        assert metadata['video_codec'] == 'h264'
        assert metadata['audio_codec'] == 'aac'
        assert metadata['audio_channels'] == 2
        assert metadata['audio_sample_rate'] == 48000
        assert metadata['bitrate'] == 5000000
        assert metadata['format_name'] == 'mp4'
        assert 'eng' in metadata['subtitle_tracks']
    
    @pytest.mark.asyncio
    async def test_extract_video_without_audio(self, video_extractor):
        """Test extracting metadata from video without audio."""
        probe_data = {
            'streams': [
                {
                    'codec_type': 'video',
                    'codec_name': 'h264',
                    'width': 1280,
                    'height': 720,
                    'r_frame_rate': '24/1',
                },
            ],
            'format': {
                'duration': '60.0',
                'bit_rate': '2000000',
                'format_name': 'mkv',
            },
        }
        
        with patch('ffmpeg.probe', return_value=probe_data):
            metadata = await video_extractor.extract(Path('test.mkv'))
        
        assert metadata['width'] == 1280
        assert metadata['height'] == 720
        assert 'audio_codec' not in metadata
    
    def test_parse_fps_fraction(self, video_extractor):
        """Test parsing FPS from fraction."""
        fps = video_extractor._parse_fps('30000/1001')
        assert abs(fps - 29.97) < 0.01
    
    def test_parse_fps_integer(self, video_extractor):
        """Test parsing FPS from integer."""
        fps = video_extractor._parse_fps('30')
        assert fps == 30.0
    
    def test_parse_fps_invalid(self, video_extractor):
        """Test parsing invalid FPS."""
        fps = video_extractor._parse_fps('invalid')
        assert fps == 0.0
    
    @pytest.mark.asyncio
    async def test_extract_ffmpeg_error(self, video_extractor):
        """Test handling FFmpeg errors."""
        import ffmpeg
        
        error = ffmpeg.Error('cmd', 'stdout', b'error message')
        with patch('ffmpeg.probe', side_effect=error):
            with pytest.raises(MetadataExtractionError) as exc_info:
                await video_extractor.extract(Path('test.mp4'))
            
            assert 'FFmpeg error' in str(exc_info.value)


# Test AudioMetadataExtractor

class TestAudioMetadataExtractor:
    """Tests for audio metadata extraction."""
    
    @pytest.fixture
    def audio_extractor(self):
        """Create audio metadata extractor."""
        return AudioMetadataExtractor()
    
    @pytest.fixture
    def mock_audio_file(self):
        """Mock mutagen audio file."""
        audio = MagicMock()
        audio.__getitem__ = Mock(side_effect=lambda key: {
            'artist': ['Test Artist'],
            'album': ['Test Album'],
            'title': ['Test Song'],
            'date': ['2024'],
            'genre': ['Rock'],
            'tracknumber': ['3/12'],
        }.get(key, []))
        audio.__contains__ = Mock(side_effect=lambda key: key in [
            'artist', 'album', 'title', 'date', 'genre', 'tracknumber'
        ])
        
        # Mock audio info
        audio.info = MagicMock()
        audio.info.length = 240.5
        audio.info.bitrate = 320000
        audio.info.sample_rate = 44100
        audio.info.channels = 2
        
        return audio
    
    @pytest.mark.asyncio
    async def test_extract_audio_metadata(self, audio_extractor, mock_audio_file):
        """Test extracting audio metadata."""
        with patch('src.core.metadata_extractor.MutagenFile', return_value=mock_audio_file):
            metadata = await audio_extractor.extract(Path('test.mp3'))
        
        assert metadata['artist'] == 'Test Artist'
        assert metadata['album'] == 'Test Album'
        assert metadata['title'] == 'Test Song'
        assert metadata['year'] == 2024
        assert metadata['genre'] == 'Rock'
        assert metadata['track_number'] == 3
        assert metadata['duration'] == 240.5
        assert metadata['bitrate'] == 320000
        assert metadata['sample_rate'] == 44100
        assert metadata['audio_channels'] == 2
    
    @pytest.mark.asyncio
    async def test_extract_audio_missing_tags(self, audio_extractor):
        """Test extracting audio with missing tags."""
        audio = MagicMock()
        audio.__contains__ = Mock(return_value=False)
        audio.info = MagicMock()
        audio.info.length = 180.0
        
        with patch('src.core.metadata_extractor.MutagenFile', return_value=audio):
            metadata = await audio_extractor.extract(Path('test.mp3'))
        
        assert metadata['artist'] is None
        assert metadata['album'] is None
        assert metadata['duration'] == 180.0
    
    def test_parse_year_full_date(self, audio_extractor):
        """Test parsing year from full date."""
        year = audio_extractor._parse_year('2024-03-15')
        assert year == 2024
    
    def test_parse_year_year_only(self, audio_extractor):
        """Test parsing year from year only."""
        year = audio_extractor._parse_year('2024')
        assert year == 2024
    
    def test_parse_year_invalid(self, audio_extractor):
        """Test parsing invalid year."""
        year = audio_extractor._parse_year('invalid')
        assert year is None
    
    def test_parse_track_number_with_total(self, audio_extractor):
        """Test parsing track number with total."""
        track = audio_extractor._parse_track_number('3/12')
        assert track == 3
    
    def test_parse_track_number_simple(self, audio_extractor):
        """Test parsing simple track number."""
        track = audio_extractor._parse_track_number('5')
        assert track == 5
    
    @pytest.mark.asyncio
    async def test_extract_audio_file_error(self, audio_extractor):
        """Test handling file read errors."""
        with patch('mutagen.File', return_value=None):
            with pytest.raises(MetadataExtractionError) as exc_info:
                await audio_extractor.extract(Path('test.mp3'))
            
            assert 'Could not read audio file' in str(exc_info.value)


# Test ImageMetadataExtractor

class TestImageMetadataExtractor:
    """Tests for image metadata extraction."""
    
    @pytest.fixture
    def image_extractor(self):
        """Create image metadata extractor."""
        return ImageMetadataExtractor()
    
    @pytest.fixture
    def mock_image(self):
        """Mock PIL Image."""
        img = MagicMock()
        img.width = 4000
        img.height = 3000
        img.format = 'JPEG'
        img.mode = 'RGB'
        
        # Mock EXIF data
        exif_data = {
            271: 'Canon',  # Make
            272: 'EOS 5D Mark IV',  # Model
            42036: 'EF 24-70mm f/2.8L',  # LensModel
            34855: 800,  # ISOSpeedRatings
            33437: (1, 250),  # FNumber (f/2.8 stored as 28/10)
            33434: (1, 250),  # ExposureTime
            37386: (50, 1),  # FocalLength
            36867: '2024:03:15 14:30:00',  # DateTimeOriginal
            274: 1,  # Orientation
        }
        img.getexif = Mock(return_value=exif_data)
        
        return img
    
    @pytest.mark.asyncio
    async def test_extract_image_metadata(self, image_extractor, mock_image):
        """Test extracting image metadata."""
        with patch('PIL.Image.open', return_value=mock_image):
            metadata = await image_extractor.extract(Path('test.jpg'))
        
        assert metadata['width'] == 4000
        assert metadata['height'] == 3000
        assert metadata['format'] == 'JPEG'
        assert metadata['mode'] == 'RGB'
        assert metadata['camera_make'] == 'Canon'
        assert metadata['camera_model'] == 'EOS 5D Mark IV'
        assert metadata['lens_model'] == 'EF 24-70mm f/2.8L'
        assert metadata['iso'] == 800
        assert metadata['orientation'] == 1
    
    @pytest.mark.asyncio
    async def test_extract_image_without_exif(self, image_extractor):
        """Test extracting image without EXIF data."""
        img = MagicMock()
        img.width = 1920
        img.height = 1080
        img.format = 'PNG'
        img.mode = 'RGBA'
        img.getexif = Mock(return_value={})
        
        with patch('PIL.Image.open', return_value=img):
            metadata = await image_extractor.extract(Path('test.png'))
        
        assert metadata['width'] == 1920
        assert metadata['height'] == 1080
        assert metadata['format'] == 'PNG'
        assert 'camera_make' not in metadata
    
    def test_parse_fnumber_tuple(self, image_extractor):
        """Test parsing f-number from tuple."""
        fnumber = image_extractor._parse_fnumber((28, 10))
        assert fnumber == 2.8
    
    def test_parse_fnumber_float(self, image_extractor):
        """Test parsing f-number from float."""
        fnumber = image_extractor._parse_fnumber(2.8)
        assert fnumber == 2.8
    
    def test_format_shutter_speed_fraction(self, image_extractor):
        """Test formatting shutter speed from fraction."""
        speed = image_extractor._format_shutter_speed((1, 250))
        assert speed == '1/250'
    
    def test_format_shutter_speed_slow(self, image_extractor):
        """Test formatting slow shutter speed."""
        speed = image_extractor._format_shutter_speed((2, 1))
        assert speed == '2.0s'
    
    def test_parse_focal_length(self, image_extractor):
        """Test parsing focal length."""
        focal = image_extractor._parse_focal_length((50, 1))
        assert focal == 50.0
    
    def test_parse_datetime(self, image_extractor):
        """Test parsing EXIF datetime."""
        dt = image_extractor._parse_datetime('2024:03:15 14:30:00')
        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 3
        assert dt.day == 15
    
    def test_parse_datetime_invalid(self, image_extractor):
        """Test parsing invalid datetime."""
        dt = image_extractor._parse_datetime('invalid')
        assert dt is None
    
    def test_convert_to_degrees(self, image_extractor):
        """Test converting GPS coordinates to degrees."""
        # 37° 46' 29.4" = 37.7748333...
        degrees = image_extractor._convert_to_degrees(
            ((37, 1), (46, 1), (294, 10))
        )
        assert abs(degrees - 37.7748) < 0.001


# Test ThumbnailGenerator

class TestThumbnailGenerator:
    """Tests for thumbnail generation."""
    
    @pytest.fixture
    def thumbnail_dir(self, tmp_path):
        """Create temporary thumbnail directory."""
        return tmp_path / "thumbnails"
    
    @pytest.fixture
    def thumbnail_generator(self, thumbnail_dir):
        """Create thumbnail generator."""
        return ThumbnailGenerator(thumbnail_dir, size=300)
    
    @pytest.mark.asyncio
    async def test_generate_video_thumbnail(self, thumbnail_generator, thumbnail_dir):
        """Test generating video thumbnail."""
        video_path = Path('test.mp4')
        media_id = 'test-uuid-123'
        
        mock_probe = {'format': {'duration': '120.0'}}
        
        with patch('ffmpeg.probe', return_value=mock_probe):
            with patch.object(
                thumbnail_generator,
                '_generate_video_thumbnail_sync',
                return_value=None
            ):
                thumb_path = await thumbnail_generator.generate_video_thumbnail(
                    video_path, media_id
                )
        
        assert thumb_path == thumbnail_dir / f"{media_id}.jpg"
    
    @pytest.mark.asyncio
    async def test_generate_video_thumbnail_custom_timestamp(
        self, thumbnail_generator, thumbnail_dir
    ):
        """Test generating video thumbnail with custom timestamp."""
        video_path = Path('test.mp4')
        media_id = 'test-uuid-456'
        timestamp = 30.0
        
        with patch.object(
            thumbnail_generator,
            '_generate_video_thumbnail_sync',
            return_value=None
        ):
            thumb_path = await thumbnail_generator.generate_video_thumbnail(
                video_path, media_id, timestamp
            )
        
        assert thumb_path == thumbnail_dir / f"{media_id}.jpg"
    
    @pytest.mark.asyncio
    async def test_generate_image_thumbnail(self, thumbnail_generator, thumbnail_dir):
        """Test generating image thumbnail."""
        image_path = Path('test.jpg')
        media_id = 'test-uuid-789'
        
        with patch.object(
            thumbnail_generator,
            '_generate_image_thumbnail_sync',
            return_value=None
        ):
            thumb_path = await thumbnail_generator.generate_image_thumbnail(
                image_path, media_id
            )
        
        assert thumb_path == thumbnail_dir / f"{media_id}.jpg"
    
    def test_correct_orientation_rotate_180(self, thumbnail_generator):
        """Test correcting image orientation (180 rotation)."""
        img = MagicMock()
        img.getexif = Mock(return_value={0x0112: 3})  # Rotated 180
        img.rotate = Mock(return_value=img)
        
        result = thumbnail_generator._correct_orientation(img)
        img.rotate.assert_called_once_with(180, expand=True)
    
    def test_correct_orientation_rotate_90_cw(self, thumbnail_generator):
        """Test correcting image orientation (90 CW)."""
        img = MagicMock()
        img.getexif = Mock(return_value={0x0112: 8})  # Rotated 90 CW
        img.rotate = Mock(return_value=img)
        
        result = thumbnail_generator._correct_orientation(img)
        img.rotate.assert_called_once_with(90, expand=True)
    
    def test_correct_orientation_no_exif(self, thumbnail_generator):
        """Test correcting orientation with no EXIF."""
        img = MagicMock()
        img.getexif = Mock(return_value={})
        
        result = thumbnail_generator._correct_orientation(img)
        assert result == img
    
    def test_delete_thumbnail_exists(self, thumbnail_generator, thumbnail_dir):
        """Test deleting existing thumbnail."""
        media_id = 'test-uuid-delete'
        thumb_path = thumbnail_dir / f"{media_id}.jpg"
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        thumb_path.touch()
        
        result = thumbnail_generator.delete_thumbnail(media_id)
        assert result is True
        assert not thumb_path.exists()
    
    def test_delete_thumbnail_not_exists(self, thumbnail_generator):
        """Test deleting non-existent thumbnail."""
        result = thumbnail_generator.delete_thumbnail('nonexistent')
        assert result is False
    
    def test_get_thumbnail_path_exists(self, thumbnail_generator, thumbnail_dir):
        """Test getting path to existing thumbnail."""
        media_id = 'test-uuid-get'
        thumb_path = thumbnail_dir / f"{media_id}.jpg"
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        thumb_path.touch()
        
        result = thumbnail_generator.get_thumbnail_path(media_id)
        assert result == thumb_path
    
    def test_get_thumbnail_path_not_exists(self, thumbnail_generator):
        """Test getting path to non-existent thumbnail."""
        result = thumbnail_generator.get_thumbnail_path('nonexistent')
        assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_thumbnail_by_type_video(self, thumbnail_generator):
        """Test generating thumbnail by media type (video)."""
        with patch.object(
            thumbnail_generator,
            'generate_video_thumbnail',
            new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = Path('thumb.jpg')
            
            result = await thumbnail_generator.generate_thumbnail(
                Path('test.mp4'), 'uuid', 'video'
            )
            
            mock_gen.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_thumbnail_by_type_image(self, thumbnail_generator):
        """Test generating thumbnail by media type (image)."""
        with patch.object(
            thumbnail_generator,
            'generate_image_thumbnail',
            new_callable=AsyncMock
        ) as mock_gen:
            mock_gen.return_value = Path('thumb.jpg')
            
            result = await thumbnail_generator.generate_thumbnail(
                Path('test.jpg'), 'uuid', 'image'
            )
            
            mock_gen.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_thumbnail_by_type_audio(self, thumbnail_generator):
        """Test generating thumbnail for audio (returns None)."""
        result = await thumbnail_generator.generate_thumbnail(
            Path('test.mp3'), 'uuid', 'audio'
        )
        
        assert result is None


# Test MetadataExtractor

class TestMetadataExtractor:
    """Tests for main metadata extraction coordinator."""
    
    @pytest.fixture
    def metadata_extractor(self, tmp_path):
        """Create metadata extractor."""
        return MetadataExtractor(tmp_path / "thumbnails")
    
    @pytest.fixture
    def mock_media_item(self, tmp_path):
        """Create mock media item."""
        # Create a temporary file
        test_file = tmp_path / "test_video.mp4"
        test_file.touch()
        
        item = MagicMock(spec=MediaItem)
        item.id = 'test-uuid-123'
        item.file_path = str(test_file)
        item.file_name = 'test_video.mp4'
        item.media_type = MediaType.video
        
        return item
    
    @pytest.mark.asyncio
    async def test_extract_all_metadata_video(
        self, metadata_extractor, mock_media_item
    ):
        """Test extracting metadata for video."""
        mock_metadata = {
            'duration': 120.5,
            'width': 1920,
            'height': 1080,
        }
        
        with patch.object(
            metadata_extractor.video_extractor,
            'extract',
            new_callable=AsyncMock,
            return_value=mock_metadata
        ):
            result = await metadata_extractor.extract_all_metadata(mock_media_item)
        
        assert result == mock_metadata
    
    @pytest.mark.asyncio
    async def test_extract_all_metadata_audio(
        self, metadata_extractor, mock_media_item, tmp_path
    ):
        """Test extracting metadata for audio."""
        test_file = tmp_path / "test_audio.mp3"
        test_file.touch()
        
        mock_media_item.file_path = str(test_file)
        mock_media_item.media_type = MediaType.audio
        
        mock_metadata = {
            'artist': 'Test Artist',
            'duration': 240.5,
        }
        
        with patch.object(
            metadata_extractor.audio_extractor,
            'extract',
            new_callable=AsyncMock,
            return_value=mock_metadata
        ):
            result = await metadata_extractor.extract_all_metadata(mock_media_item)
        
        assert result == mock_metadata
    
    @pytest.mark.asyncio
    async def test_extract_all_metadata_image(
        self, metadata_extractor, mock_media_item, tmp_path
    ):
        """Test extracting metadata for image."""
        test_file = tmp_path / "test_image.jpg"
        test_file.touch()
        
        mock_media_item.file_path = str(test_file)
        mock_media_item.media_type = MediaType.image
        
        mock_metadata = {
            'width': 4000,
            'height': 3000,
        }
        
        with patch.object(
            metadata_extractor.image_extractor,
            'extract',
            new_callable=AsyncMock,
            return_value=mock_metadata
        ):
            result = await metadata_extractor.extract_all_metadata(mock_media_item)
        
        assert result == mock_metadata
    
    @pytest.mark.asyncio
    async def test_extract_all_metadata_file_not_found(
        self, metadata_extractor, mock_media_item
    ):
        """Test extracting metadata for non-existent file."""
        mock_media_item.file_path = '/nonexistent/file.mp4'
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            await metadata_extractor.extract_all_metadata(mock_media_item)
        
        assert 'File not found' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_batch_extract(self, metadata_extractor, tmp_path):
        """Test batch metadata extraction."""
        # Create mock media items
        items = []
        for i in range(3):
            test_file = tmp_path / f"test_{i}.mp4"
            test_file.touch()
            
            item = MagicMock(spec=MediaItem)
            item.id = f'uuid-{i}'
            item.file_path = str(test_file)
            item.file_name = f'test_{i}.mp4'
            item.media_type = MediaType.video
            items.append(item)
        
        mock_metadata = {'duration': 120.0}
        
        with patch.object(
            metadata_extractor.video_extractor,
            'extract',
            new_callable=AsyncMock,
            return_value=mock_metadata
        ):
            results = await metadata_extractor.batch_extract(items)
        
        assert len(results) == 3
        for i in range(3):
            assert f'uuid-{i}' in results
            assert results[f'uuid-{i}'] == mock_metadata
    
    @pytest.mark.asyncio
    async def test_batch_extract_with_progress(self, metadata_extractor, tmp_path):
        """Test batch extraction with progress callback."""
        items = []
        for i in range(2):
            test_file = tmp_path / f"test_{i}.mp4"
            test_file.touch()
            
            item = MagicMock(spec=MediaItem)
            item.id = f'uuid-{i}'
            item.file_path = str(test_file)
            item.file_name = f'test_{i}.mp4'
            item.media_type = MediaType.video
            items.append(item)
        
        progress_calls = []
        
        def progress_callback(processed, total):
            progress_calls.append((processed, total))
        
        with patch.object(
            metadata_extractor.video_extractor,
            'extract',
            new_callable=AsyncMock,
            return_value={}
        ):
            await metadata_extractor.batch_extract(items, progress_callback)
        
        assert len(progress_calls) == 2
        assert progress_calls[0] == (1, 2)
        assert progress_calls[1] == (2, 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
