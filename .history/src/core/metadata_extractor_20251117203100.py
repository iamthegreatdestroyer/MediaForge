"""Metadata extraction system for video, audio, and image files.

Extracts comprehensive metadata using FFmpeg, Mutagen, and PIL.
"""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import ffmpeg
from mutagen import File as MutagenFile
from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

from src.models.media import MediaItem, MediaType
from src.models.metadata import MediaMetadata

logger = logging.getLogger(__name__)


class MetadataExtractionError(Exception):
    """Base exception for metadata extraction errors."""
    pass


class VideoMetadataExtractor:
    """Extract metadata from video files using FFmpeg."""
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive video metadata.
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary containing video metadata:
            - duration: Duration in seconds
            - width: Video width in pixels
            - height: Video height in pixels
            - fps: Frames per second
            - video_codec: Video codec name
            - audio_codec: Audio codec name
            - bitrate: Bitrate in bits per second
            - format_name: Container format
            - audio_channels: Number of audio channels
            - audio_sample_rate: Audio sample rate in Hz
            - subtitle_tracks: List of subtitle language codes
            
        Raises:
            MetadataExtractionError: If extraction fails
        """
        try:
            # Run ffprobe in executor to avoid blocking
            loop = asyncio.get_event_loop()
            probe = await loop.run_in_executor(
                None, ffmpeg.probe, str(file_path)
            )
            
            # Extract stream information
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
            subtitle_streams = [
                s for s in probe['streams'] 
                if s['codec_type'] == 'subtitle'
            ]
            
            # Build metadata dictionary
            metadata = {
                'duration': float(probe['format'].get('duration', 0)),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'format_name': probe['format'].get('format_name', ''),
            }
            
            # Add video-specific data
            if video_stream:
                metadata.update({
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'video_codec': video_stream.get('codec_name', ''),
                    'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                })
            
            # Add audio-specific data
            if audio_stream:
                metadata.update({
                    'audio_codec': audio_stream.get('codec_name', ''),
                    'audio_channels': int(audio_stream.get('channels', 0)),
                    'audio_sample_rate': int(audio_stream.get('sample_rate', 0)),
                })
            
            # Add subtitle information
            metadata['subtitle_tracks'] = [
                s.get('tags', {}).get('language', 'und')
                for s in subtitle_streams
            ]
            
            logger.debug(f"Extracted video metadata from {file_path.name}")
            return metadata
            
        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if e.stderr else "Unknown error"
            raise MetadataExtractionError(f"FFmpeg error: {stderr}")
        except Exception as e:
            raise MetadataExtractionError(f"Error extracting video metadata: {str(e)}")
    
    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS from FFmpeg format (e.g., '30000/1001').
        
        Args:
            fps_str: FPS string in format "numerator/denominator"
            
        Returns:
            FPS as float
        """
        try:
            if '/' in fps_str:
                num, denom = fps_str.split('/')
                return float(num) / float(denom)
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            logger.warning(f"Could not parse FPS: {fps_str}")
            return 0.0


class AudioMetadataExtractor:
    """Extract metadata from audio files using Mutagen."""
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """Extract audio tags and technical metadata.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary containing audio metadata:
            - artist: Artist name
            - album: Album title
            - title: Song title
            - year: Release year
            - genre: Genre
            - track_number: Track number
            - duration: Duration in seconds
            - bitrate: Bitrate in bits per second
            - sample_rate: Sample rate in Hz
            - audio_channels: Number of channels
            
        Raises:
            MetadataExtractionError: If extraction fails
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(
                None, MutagenFile, str(file_path), True
            )
            
            if audio is None:
                raise MetadataExtractionError("Could not read audio file")
            
            # Extract tags
            metadata = {
                'artist': self._get_tag(audio, 'artist') or self._get_tag(audio, 'albumartist'),
                'album': self._get_tag(audio, 'album'),
                'title': self._get_tag(audio, 'title'),
                'year': self._parse_year(self._get_tag(audio, 'date')),
                'genre': self._get_tag(audio, 'genre'),
                'track_number': self._parse_track_number(self._get_tag(audio, 'tracknumber')),
                'disc_number': self._parse_track_number(self._get_tag(audio, 'discnumber')),
                'composer': self._get_tag(audio, 'composer'),
                'comment': self._get_tag(audio, 'comment'),
                'lyrics': self._get_tag(audio, 'lyrics'),
                'publisher': self._get_tag(audio, 'publisher'),
                'encoder': self._get_tag(audio, 'encoder'),
            }
            
            # Extract technical information
            if hasattr(audio, 'info'):
                if hasattr(audio.info, 'length'):
                    metadata['duration'] = float(audio.info.length)
                if hasattr(audio.info, 'bitrate'):
                    metadata['bitrate'] = int(audio.info.bitrate)
                if hasattr(audio.info, 'sample_rate'):
                    metadata['sample_rate'] = int(audio.info.sample_rate)
                if hasattr(audio.info, 'channels'):
                    metadata['audio_channels'] = int(audio.info.channels)
            
            logger.debug(f"Extracted audio metadata from {file_path.name}")
            return metadata
            
        except Exception as e:
            raise MetadataExtractionError(f"Error reading audio tags: {str(e)}")
    
    def _get_tag(self, audio: MutagenFile, key: str) -> Optional[str]:
        """Safely get tag value.
        
        Args:
            audio: Mutagen audio file object
            key: Tag key to retrieve
            
        Returns:
            Tag value or None
        """
        try:
            if key in audio:
                value = audio[key]
                if isinstance(value, list) and value:
                    return str(value[0])
                return str(value)
        except Exception:
            pass
        return None
    
    def _parse_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string.
        
        Args:
            date_str: Date string (e.g., "2024", "2024-03-15")
            
        Returns:
            Year as integer or None
        """
        if not date_str:
            return None
        
        try:
            # Try to extract 4-digit year
            match = re.search(r'\d{4}', date_str)
            if match:
                return int(match.group())
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _parse_track_number(self, track_str: Optional[str]) -> Optional[int]:
        """Parse track number from string.
        
        Args:
            track_str: Track string (e.g., "3", "3/12")
            
        Returns:
            Track number as integer or None
        """
        if not track_str:
            return None
        
        try:
            # Handle "3/12" format
            if '/' in track_str:
                track_str = track_str.split('/')[0]
            return int(track_str)
        except ValueError:
            return None


class ImageMetadataExtractor:
    """Extract EXIF metadata from images."""
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """Extract image EXIF data and technical info.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Dictionary containing image metadata:
            - width: Image width in pixels
            - height: Image height in pixels
            - format: Image format (JPEG, PNG, etc.)
            - mode: Color mode (RGB, RGBA, etc.)
            - camera_make: Camera manufacturer
            - camera_model: Camera model
            - lens_model: Lens model
            - iso: ISO speed
            - aperture: Aperture f-number
            - shutter_speed: Shutter speed string
            - focal_length: Focal length in mm
            - date_taken: Date/time photo was taken
            - latitude: GPS latitude
            - longitude: GPS longitude
            - orientation: EXIF orientation value
            
        Raises:
            MetadataExtractionError: If extraction fails
        """
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            metadata = await loop.run_in_executor(
                None, self._extract_sync, file_path
            )
            
            logger.debug(f"Extracted image metadata from {file_path.name}")
            return metadata
            
        except Exception as e:
            raise MetadataExtractionError(f"Error reading image EXIF: {str(e)}")
    
    def _extract_sync(self, file_path: Path) -> Dict[str, Any]:
        """Synchronous EXIF extraction (called in executor).
        
        Args:
            file_path: Path to image file
            
        Returns:
            Metadata dictionary
        """
        with Image.open(file_path) as img:
            # Basic image info
            metadata = {
                'width': img.width,
                'height': img.height,
                'format': img.format or 'Unknown',
                'mode': img.mode,
            }
            
            # Extract EXIF data
            try:
                exif_data = img.getexif()
                if exif_data:
                    self._process_exif_tags(exif_data, metadata)
            except Exception as e:
                logger.warning(f"Could not read EXIF data: {e}")
            
            return metadata
    
    def _process_exif_tags(
        self,
        exif_data: Dict[int, Any],
        metadata: Dict[str, Any]
    ) -> None:
        """Process EXIF tags and add to metadata.
        
        Args:
            exif_data: EXIF dictionary
            metadata: Metadata dictionary to update
        """
        for tag_id, value in exif_data.items():
            try:
                tag_name = TAGS.get(tag_id, tag_id)
                
                if tag_name == 'Make':
                    metadata['camera_make'] = str(value).strip()
                elif tag_name == 'Model':
                    metadata['camera_model'] = str(value).strip()
                elif tag_name == 'LensModel':
                    metadata['lens_model'] = str(value).strip()
                elif tag_name == 'ISOSpeedRatings':
                    metadata['iso'] = int(value)
                elif tag_name == 'FNumber':
                    metadata['aperture'] = self._parse_fnumber(value)
                elif tag_name == 'ExposureTime':
                    metadata['shutter_speed'] = self._format_shutter_speed(value)
                elif tag_name == 'FocalLength':
                    metadata['focal_length'] = self._parse_focal_length(value)
                elif tag_name == 'DateTimeOriginal':
                    metadata['date_taken'] = self._parse_datetime(value)
                elif tag_name == 'Orientation':
                    metadata['orientation'] = int(value)
                elif tag_name == 'GPSInfo':
                    gps_data = self._parse_gps(value)
                    metadata.update(gps_data)
            except Exception as e:
                logger.debug(f"Could not process EXIF tag {tag_name}: {e}")
    
    def _parse_fnumber(self, value: Any) -> Optional[float]:
        """Parse aperture f-number.
        
        Args:
            value: F-number value (tuple or float)
            
        Returns:
            F-number as float or None
        """
        try:
            if isinstance(value, tuple) and len(value) == 2:
                return float(value[0]) / float(value[1])
            return float(value)
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    
    def _format_shutter_speed(self, value: Any) -> Optional[str]:
        """Format shutter speed as string.
        
        Args:
            value: Shutter speed value (tuple or float)
            
        Returns:
            Formatted shutter speed (e.g., "1/250") or None
        """
        try:
            if isinstance(value, tuple) and len(value) == 2:
                num, denom = value
                if num == 1:
                    return f"1/{denom}"
                speed = float(num) / float(denom)
                if speed >= 1:
                    return f"{speed:.1f}s"
                return f"1/{int(1/speed)}"
            
            speed = float(value)
            if speed >= 1:
                return f"{speed:.1f}s"
            return f"1/{int(1/speed)}"
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    
    def _parse_focal_length(self, value: Any) -> Optional[float]:
        """Parse focal length.
        
        Args:
            value: Focal length value (tuple or float)
            
        Returns:
            Focal length in mm or None
        """
        try:
            if isinstance(value, tuple) and len(value) == 2:
                return float(value[0]) / float(value[1])
            return float(value)
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    
    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """Parse EXIF datetime string.
        
        Args:
            value: Datetime string (e.g., "2024:03:15 14:30:00")
            
        Returns:
            Datetime object or None
        """
        try:
            # EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
        except (ValueError, TypeError):
            return None
    
    def _parse_gps(self, gps_info: Dict) -> Dict[str, float]:
        """Parse GPS coordinates from EXIF.
        
        Args:
            gps_info: GPS info dictionary
            
        Returns:
            Dictionary with latitude and longitude
        """
        gps_data = {}
        
        try:
            # Extract GPS tags
            gps_latitude = gps_info.get(2)  # GPSLatitude
            gps_latitude_ref = gps_info.get(1)  # GPSLatitudeRef
            gps_longitude = gps_info.get(4)  # GPSLongitude
            gps_longitude_ref = gps_info.get(3)  # GPSLongitudeRef
            
            if gps_latitude and gps_longitude:
                lat = self._convert_to_degrees(gps_latitude)
                lon = self._convert_to_degrees(gps_longitude)
                
                # Apply hemisphere
                if gps_latitude_ref and gps_latitude_ref == 'S':
                    lat = -lat
                if gps_longitude_ref and gps_longitude_ref == 'W':
                    lon = -lon
                
                gps_data['latitude'] = lat
                gps_data['longitude'] = lon
        except Exception as e:
            logger.debug(f"Could not parse GPS data: {e}")
        
        return gps_data
    
    def _convert_to_degrees(self, value: tuple) -> float:
        """Convert GPS coordinates to degrees.
        
        Args:
            value: Tuple of (degrees, minutes, seconds)
            
        Returns:
            Decimal degrees
        """
        d, m, s = value
        
        # Handle rational numbers (tuples)
        if isinstance(d, tuple):
            d = float(d[0]) / float(d[1])
        if isinstance(m, tuple):
            m = float(m[0]) / float(m[1])
        if isinstance(s, tuple):
            s = float(s[0]) / float(s[1])
        
        return float(d) + (float(m) / 60.0) + (float(s) / 3600.0)


class MetadataExtractor:
    """Coordinate metadata extraction across all file types."""
    
    def __init__(self, thumbnail_dir: Optional[Path] = None):
        """Initialize metadata extractor.
        
        Args:
            thumbnail_dir: Directory for thumbnails (optional for now)
        """
        self.video_extractor = VideoMetadataExtractor()
        self.audio_extractor = AudioMetadataExtractor()
        self.image_extractor = ImageMetadataExtractor()
        self.thumbnail_dir = thumbnail_dir
    
    async def extract_all_metadata(
        self,
        media_item: MediaItem
    ) -> Dict[str, Any]:
        """Extract all metadata for a media item.
        
        Args:
            media_item: MediaItem database object
            
        Returns:
            Dictionary of extracted metadata
            
        Raises:
            MetadataExtractionError: If extraction fails
        """
        file_path = Path(media_item.file_path)
        
        if not file_path.exists():
            raise MetadataExtractionError(f"File not found: {file_path}")
        
        try:
            # Extract based on media type
            if media_item.media_type == MediaType.video:
                metadata_dict = await self.video_extractor.extract(file_path)
            
            elif media_item.media_type == MediaType.audio:
                metadata_dict = await self.audio_extractor.extract(file_path)
            
            elif media_item.media_type == MediaType.image:
                metadata_dict = await self.image_extractor.extract(file_path)
            
            else:
                metadata_dict = {}
            
            logger.info(
                f"Extracted metadata for {media_item.file_name} "
                f"({media_item.media_type.value})"
            )
            
            return metadata_dict
            
        except MetadataExtractionError:
            raise
        except Exception as e:
            raise MetadataExtractionError(
                f"Unexpected error extracting metadata: {str(e)}"
            )
    
    async def batch_extract(
        self,
        media_items: List[MediaItem],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Extract metadata for multiple items in parallel.
        
        Args:
            media_items: List of MediaItem objects
            progress_callback: Optional callback(processed, total)
            
        Returns:
            Dictionary mapping media_item.id to metadata dict
        """
        results = {}
        total = len(media_items)
        
        for i, media_item in enumerate(media_items, 1):
            try:
                metadata = await self.extract_all_metadata(media_item)
                results[str(media_item.id)] = metadata
            except MetadataExtractionError as e:
                logger.error(f"Failed to extract metadata for {media_item.file_name}: {e}")
                results[str(media_item.id)] = {}
            
            if progress_callback:
                progress_callback(i, total)
        
        return results
