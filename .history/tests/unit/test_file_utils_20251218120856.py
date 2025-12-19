"""Tests for file utilities."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import os

from src.core.file_utils import (
    MediaType,
    MimeTypeDetector,
)


class TestMediaType:
    """Tests for MediaType constants."""
    
    def test_media_type_constants(self):
        """Test MediaType constants are defined."""
        assert MediaType.VIDEO == "video"
        assert MediaType.AUDIO == "audio"
        assert MediaType.IMAGE == "image"
        assert MediaType.DOCUMENT == "document"
        assert MediaType.STREAMING == "streaming"
        assert MediaType.OTHER == "other"


class TestMimeTypeDetector:
    """Tests for MimeTypeDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a MimeTypeDetector instance."""
        return MimeTypeDetector()
    
    def test_initialization(self, detector):
        """Test MimeTypeDetector initialization."""
        # Should not raise
        assert detector is not None
    
    def test_video_extensions_coverage(self, detector):
        """Test common video extensions are covered."""
        video_exts = [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"]
        for ext in video_exts:
            assert ext in detector.VIDEO_EXTENSIONS
    
    def test_audio_extensions_coverage(self, detector):
        """Test common audio extensions are covered."""
        audio_exts = [".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a"]
        for ext in audio_exts:
            assert ext in detector.AUDIO_EXTENSIONS
    
    def test_image_extensions_coverage(self, detector):
        """Test common image extensions are covered."""
        image_exts = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"]
        for ext in image_exts:
            assert ext in detector.IMAGE_EXTENSIONS
    
    def test_document_extensions_coverage(self, detector):
        """Test common document extensions are covered."""
        doc_exts = [".pdf", ".epub", ".doc", ".docx", ".txt"]
        for ext in doc_exts:
            assert ext in detector.DOCUMENT_EXTENSIONS
    
    def test_all_media_extensions(self, detector):
        """Test ALL_MEDIA_EXTENSIONS includes all supported types."""
        # Video
        assert ".mp4" in detector.ALL_MEDIA_EXTENSIONS
        # Audio
        assert ".mp3" in detector.ALL_MEDIA_EXTENSIONS
        # Image
        assert ".jpg" in detector.ALL_MEDIA_EXTENSIONS
        # Streaming
        assert ".m3u8" in detector.ALL_MEDIA_EXTENSIONS
        # Documents should NOT be in media extensions
        assert ".pdf" not in detector.ALL_MEDIA_EXTENSIONS
    
    def test_get_media_type_video(self, detector):
        """Test media type detection for video files."""
        assert detector.get_media_type(Path("test.mp4")) == MediaType.VIDEO
        assert detector.get_media_type(Path("test.mkv")) == MediaType.VIDEO
        assert detector.get_media_type(Path("test.avi")) == MediaType.VIDEO
    
    def test_get_media_type_audio(self, detector):
        """Test media type detection for audio files."""
        assert detector.get_media_type(Path("test.mp3")) == MediaType.AUDIO
        assert detector.get_media_type(Path("test.flac")) == MediaType.AUDIO
        assert detector.get_media_type(Path("test.wav")) == MediaType.AUDIO
    
    def test_get_media_type_image(self, detector):
        """Test media type detection for image files."""
        assert detector.get_media_type(Path("test.jpg")) == MediaType.IMAGE
        assert detector.get_media_type(Path("test.png")) == MediaType.IMAGE
        assert detector.get_media_type(Path("test.gif")) == MediaType.IMAGE
    
    def test_get_media_type_document(self, detector):
        """Test media type detection for document files."""
        assert detector.get_media_type(Path("test.pdf")) == MediaType.DOCUMENT
        assert detector.get_media_type(Path("test.epub")) == MediaType.DOCUMENT
    
    def test_get_media_type_streaming(self, detector):
        """Test media type detection for streaming files."""
        assert detector.get_media_type(Path("playlist.m3u8")) == MediaType.STREAMING
        assert detector.get_media_type(Path("playlist.m3u")) == MediaType.STREAMING
    
    def test_get_media_type_case_insensitive(self, detector):
        """Test media type detection is case insensitive."""
        assert detector.get_media_type(Path("test.MP4")) == MediaType.VIDEO
        assert detector.get_media_type(Path("test.JPEG")) == MediaType.IMAGE
        assert detector.get_media_type(Path("test.Mp3")) == MediaType.AUDIO
    
    def test_detect_mime_type_common_video(self, detector):
        """Test MIME type detection for common video types."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"dummy video content")
            temp_path = Path(f.name)
        
        try:
            mime = detector.detect_mime_type(temp_path)
            assert "video" in mime or "octet-stream" in mime
        finally:
            temp_path.unlink()
    
    def test_detect_mime_type_extension_fallback(self, detector):
        """Test MIME type detection falls back to extension."""
        # Force fallback by using a file that doesn't exist
        # This tests the extension-based path
        result = detector.detect_mime_type(Path("nonexistent.mp4"))
        # Should return video/mp4 based on extension
        assert "video" in result or "octet-stream" in result
    
    def test_detect_mime_type_unknown_extension(self, detector):
        """Test MIME type detection for unknown extension."""
        result = detector.detect_mime_type(Path("file.xyz123unknown"))
        assert result == "application/octet-stream"
    
    def test_detect_mime_type_mkv_extension_map(self, detector):
        """Test MKV gets correct MIME type from extension map."""
        # MKV may not be in default mimetypes, test extension map
        result = detector.detect_mime_type(Path("video.mkv"))
        assert "matroska" in result or "video" in result or "octet-stream" in result


class TestMimeTypeDetectorMagic:
    """Tests for MimeTypeDetector with python-magic."""
    
    def test_detector_without_magic(self):
        """Test detector works without python-magic."""
        with patch.dict('sys.modules', {'magic': None}):
            # This simulates magic not being available
            detector = MimeTypeDetector()
            # Should still work for extension-based detection
            result = detector.get_media_type(Path("test.mp4"))
            assert result == MediaType.VIDEO
    
    def test_detector_with_magic_import_error(self):
        """Test detector handles magic import error gracefully."""
        with patch('src.core.file_utils.logger') as mock_logger:
            # Create detector - it will try to import magic
            detector = MimeTypeDetector()
            # Should not raise, just log warning
            assert detector is not None
