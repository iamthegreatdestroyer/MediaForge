"""File utility functions for media scanning and detection.

Provides MIME type detection, media type classification, file traversal,
and platform-agnostic utilities for the media scanner.
"""

from __future__ import annotations

import logging
import mimetypes
import sys
from pathlib import Path
from typing import List, Set, Optional

logger = logging.getLogger(__name__)

# Initialize mimetypes
mimetypes.init()


class MediaType:
    """Media type classification constants"""
    
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    STREAMING = "streaming"
    OTHER = "other"


class MimeTypeDetector:
    """Detect MIME types using file extensions and classify media types.
    
    Uses python-magic as fallback for magic byte detection when available.
    Falls back to extension-based detection for maximum compatibility.
    """
    
    # Comprehensive extension mappings
    VIDEO_EXTENSIONS: Set[str] = {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".mts",
        ".m2ts", ".vob", ".divx", ".xvid", ".rm", ".rmvb", ".asf"
    }
    
    AUDIO_EXTENSIONS: Set[str] = {
        ".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma",
        ".opus", ".ape", ".alac", ".aiff", ".aif", ".ac3", ".dts",
        ".mka", ".mpc", ".tta", ".wv", ".ra", ".mid", ".midi"
    }
    
    IMAGE_EXTENSIONS: Set[str] = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
        ".tiff", ".tif", ".heic", ".heif", ".raw", ".cr2", ".nef",
        ".arw", ".dng", ".orf", ".rw2", ".pef", ".srw", ".ico",
        ".psd", ".xcf", ".jxr", ".avif", ".jfif"
    }
    
    DOCUMENT_EXTENSIONS: Set[str] = {
        ".pdf", ".epub", ".mobi", ".azw3", ".djvu", ".cbr", ".cbz",
        ".cb7", ".cbt", ".doc", ".docx", ".txt", ".rtf", ".odt"
    }
    
    STREAMING_EXTENSIONS: Set[str] = {
        ".m3u8", ".m3u", ".pls", ".strm", ".asx", ".xspf"
    }
    
    # Supported media extensions (video, audio, image, streaming only)
    ALL_MEDIA_EXTENSIONS: Set[str] = (
        VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | IMAGE_EXTENSIONS | STREAMING_EXTENSIONS
    )
    
    def __init__(self):
        """Initialize MIME detector with optional python-magic support."""
        self.magic = None
        try:
            import magic
            self.magic = magic.Magic(mime=True)
            logger.debug("python-magic loaded successfully")
        except (ImportError, OSError) as e:
            logger.warning(
                f"python-magic not available, using extension-based detection: {e}"
            )
    
    def detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type using magic bytes if available, else extension.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            MIME type string (e.g., 'video/mp4', 'audio/mpeg')
        """
        # Try magic bytes first if available
        if self.magic:
            try:
                mime_type = self.magic.from_file(str(file_path))
                if mime_type and mime_type != "application/octet-stream":
                    return mime_type
            except Exception as e:
                logger.debug(
                    f"Magic byte detection failed for {file_path}: {e}"
                )
        
        # Fallback to extension-based detection
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type
        
        # Map common extensions manually
        ext = file_path.suffix.lower()
        extension_map = {
            ".mkv": "video/x-matroska",
            ".flac": "audio/flac",
            ".opus": "audio/opus",
            ".webp": "image/webp",
            ".heic": "image/heic",
            ".m3u8": "application/x-mpegURL",
            ".strm": "application/x-stream"
        }
        
        return extension_map.get(ext, "application/octet-stream")
    
    def get_media_type(self, file_path: Path) -> str:
        """Classify file into media type category.
        
        Args:
            file_path: Path to file to classify
            
        Returns:
            Media type string from MediaType constants
        """
        ext = file_path.suffix.lower()
        
        if ext in self.VIDEO_EXTENSIONS:
            return MediaType.VIDEO
        elif ext in self.AUDIO_EXTENSIONS:
            return MediaType.AUDIO
        elif ext in self.IMAGE_EXTENSIONS:
            return MediaType.IMAGE
        elif ext in self.DOCUMENT_EXTENSIONS:
            return MediaType.DOCUMENT
        elif ext in self.STREAMING_EXTENSIONS:
            return MediaType.STREAMING
        else:
            # Try MIME-based classification as fallback
            mime = self.detect_mime_type(file_path)
            if mime.startswith("video/"):
                return MediaType.VIDEO
            elif mime.startswith("audio/"):
                return MediaType.AUDIO
            elif mime.startswith("image/"):
                return MediaType.IMAGE
            else:
                return MediaType.OTHER
    
    def is_media_file(self, file_path: Path) -> bool:
        """Check if file is a supported media type.
        
        Args:
            file_path: Path to file to check
            
        Returns:
            True if file extension matches supported media types
        """
        return file_path.suffix.lower() in self.ALL_MEDIA_EXTENSIONS


def get_all_files(
    root_dir: Path,
    recursive: bool = True,
    include_hidden: bool = False,
    extensions: Optional[Set[str]] = None
) -> List[Path]:
    """Get all files in directory matching criteria.
    
    Args:
        root_dir: Root directory to scan
        recursive: If True, scan subdirectories recursively
        include_hidden: If True, include hidden files and directories
        extensions: Optional set of file extensions to filter (e.g., {'.mp4', '.mkv'})
        
    Returns:
        List of Path objects for all matching files
        
    Raises:
        ValueError: If root_dir doesn't exist or isn't a directory
    """
    if not root_dir.exists():
        raise ValueError(f"Directory does not exist: {root_dir}")
    
    if not root_dir.is_dir():
        raise ValueError(f"Path is not a directory: {root_dir}")
    
    files: List[Path] = []
    
    try:
        if recursive:
            # Use rglob for recursive scanning
            pattern = "**/*"
            paths = root_dir.rglob("*")
        else:
            # Use glob for non-recursive scanning
            paths = root_dir.glob("*")
        
        for path in paths:
            try:
                # Skip if not a file
                if not path.is_file():
                    continue
                
                # Skip hidden files/directories if requested
                if not include_hidden and is_hidden(path):
                    continue
                
                # Filter by extensions if specified
                if extensions and path.suffix.lower() not in extensions:
                    continue
                
                files.append(path)
                
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot access {path}: {e}")
                continue
                
    except (PermissionError, OSError) as e:
        logger.error(f"Cannot access directory {root_dir}: {e}")
    
    return files


def is_hidden(file_path: Path) -> bool:
    """Check if file or any parent directory is hidden.
    
    Cross-platform implementation that works on Windows, macOS, and Linux.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file or any parent directory is hidden
    """
    # Check each part of the path
    for part in file_path.parts:
        if part.startswith('.'):
            return True
    
    # Windows-specific hidden file check
    if sys.platform == 'win32':
        try:
            import ctypes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
            # FILE_ATTRIBUTE_HIDDEN = 0x2
            if attrs != -1 and bool(attrs & 0x2):
                return True
        except (ImportError, AttributeError, OSError):
            pass
    
    return False


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., '1.5 MB', '3.2 GB')
    """
    if size_bytes < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


__all__ = [
    "MediaType",
    "MimeTypeDetector",
    "get_all_files",
    "is_hidden",
    "format_file_size",
]
