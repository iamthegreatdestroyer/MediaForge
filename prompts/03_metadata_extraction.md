# Prompt 03: Metadata Extraction Implementation

## Metadata
- **Phase**: Foundation  
- **Priority**: Critical
- **Estimated Time**: 4-5 hours
- **Dependencies**: Prompt 01 (Database), Prompt 02 (Scanner)
- **Files to Create**: `src/core/metadata_extractor.py`, `src/core/thumbnail_generator.py`

---

# GITHUB COPILOT PROMPT: METADATA EXTRACTION IMPLEMENTATION

## Context

You are implementing a comprehensive metadata extraction system for MediaForge that extracts rich metadata from video, audio, and image files using FFmpeg, Pillow, and other libraries. The system must handle:
- Video: resolution, duration, codecs, bitrate, fps, subtitle tracks
- Audio: artist, album, title, year, genre, duration, bitrate, sample rate
- Images: EXIF data, dimensions, camera info, GPS coordinates
- Thumbnails: Generate preview images for videos and images

## Technical Requirements

### Core Components

1. **MetadataExtractor**: Main extraction orchestrator
2. **VideoMetadataExtractor**: FFmpeg-based video analysis
3. **AudioMetadataExtractor**: TagLib/Mutagen for audio tags
4. **ImageMetadataExtractor**: EXIF extraction
5. **ThumbnailGenerator**: Create preview images

### FFmpeg Integration

Use `ffmpeg-python` for video/audio analysis:

```python
import ffmpeg
from typing import Dict, Any, Optional
from pathlib import Path

class VideoMetadataExtractor:
    """Extract metadata from video files using FFmpeg"""
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract comprehensive video metadata
        
        Returns:
            {
                'duration': 120.5,  # seconds
                'width': 1920,
                'height': 1080,
                'fps': 29.97,
                'video_codec': 'h264',
                'audio_codec': 'aac',
                'bitrate': 5000000,  # bits per second
                'format_name': 'mp4',
                'audio_channels': 2,
                'audio_sample_rate': 48000,
                'subtitle_tracks': ['eng', 'spa'],
                'has_chapters': True,
                'creation_time': datetime(...),
                'file_size': 500000000
            }
        """
        try:
            # Use ffprobe to get file information
            probe = ffmpeg.probe(str(file_path))
            
            # Extract video stream info
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            # Extract audio stream info
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
            # Extract subtitle tracks
            subtitle_streams = [
                s for s in probe['streams'] 
                if s['codec_type'] == 'subtitle'
            ]
            
            # Build metadata dict
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
                    'fps': self._parse_fps(video_stream.get('r_frame_rate', '')),
                })
            
            # Add audio-specific data
            if audio_stream:
                metadata.update({
                    'audio_codec': audio_stream.get('codec_name', ''),
                    'audio_channels': int(audio_stream.get('channels', 0)),
                    'audio_sample_rate': int(audio_stream.get('sample_rate', 0)),
                })
            
            # Add subtitle info
            metadata['subtitle_tracks'] = [
                s.get('tags', {}).get('language', 'und')
                for s in subtitle_streams
            ]
            
            return metadata
            
        except ffmpeg.Error as e:
            # Handle FFmpeg errors
            raise MetadataExtractionError(f"FFmpeg error: {e.stderr.decode()}")
    
    def _parse_fps(self, fps_str: str) -> float:
        """Parse FPS from FFmpeg format (e.g., '30000/1001')"""
        pass
```

### Audio Metadata Extraction

```python
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

class AudioMetadataExtractor:
    """Extract metadata from audio files"""
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract audio tags and technical metadata
        
        Returns:
            {
                'artist': 'Artist Name',
                'album': 'Album Title',
                'title': 'Song Title',
                'year': 2024,
                'genre': 'Rock',
                'track_number': 3,
                'total_tracks': 12,
                'duration': 240.5,
                'bitrate': 320000,
                'sample_rate': 44100,
                'channels': 2,
                'codec': 'mp3'
            }
        """
        try:
            audio = MutagenFile(str(file_path), easy=True)
            
            if audio is None:
                raise MetadataExtractionError("Could not read audio file")
            
            # Extract tags
            metadata = {
                'artist': self._get_tag(audio, 'artist'),
                'album': self._get_tag(audio, 'album'),
                'title': self._get_tag(audio, 'title'),
                'year': self._parse_year(self._get_tag(audio, 'date')),
                'genre': self._get_tag(audio, 'genre'),
                'track_number': self._parse_track_number(self._get_tag(audio, 'tracknumber')),
            }
            
            # Extract technical info
            if hasattr(audio.info, 'length'):
                metadata['duration'] = audio.info.length
            if hasattr(audio.info, 'bitrate'):
                metadata['bitrate'] = audio.info.bitrate
            if hasattr(audio.info, 'sample_rate'):
                metadata['sample_rate'] = audio.info.sample_rate
            if hasattr(audio.info, 'channels'):
                metadata['channels'] = audio.info.channels
            
            return metadata
            
        except Exception as e:
            raise MetadataExtractionError(f"Error reading audio tags: {str(e)}")
    
    def _get_tag(self, audio: MutagenFile, key: str) -> Optional[str]:
        """Safely get tag value"""
        pass
    
    def _parse_year(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from date string"""
        pass
```

### Image Metadata Extraction

```python
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif

class ImageMetadataExtractor:
    """Extract EXIF metadata from images"""
    
    async def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract image EXIF data and technical info
        
        Returns:
            {
                'width': 4000,
                'height': 3000,
                'format': 'JPEG',
                'mode': 'RGB',
                'camera_make': 'Canon',
                'camera_model': 'EOS 5D Mark IV',
                'lens_model': 'EF 24-70mm f/2.8L',
                'iso': 800,
                'aperture': 2.8,
                'shutter_speed': '1/250',
                'focal_length': 50.0,
                'date_taken': datetime(...),
                'latitude': 37.7749,
                'longitude': -122.4194,
                'orientation': 1
            }
        """
        try:
            with Image.open(file_path) as img:
                # Basic image info
                metadata = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                }
                
                # Extract EXIF data
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        
                        # Map EXIF tags to our schema
                        if tag_name == 'Make':
                            metadata['camera_make'] = value
                        elif tag_name == 'Model':
                            metadata['camera_model'] = value
                        elif tag_name == 'LensModel':
                            metadata['lens_model'] = value
                        elif tag_name == 'ISOSpeedRatings':
                            metadata['iso'] = value
                        elif tag_name == 'FNumber':
                            metadata['aperture'] = self._parse_fnumber(value)
                        elif tag_name == 'ExposureTime':
                            metadata['shutter_speed'] = self._format_shutter_speed(value)
                        elif tag_name == 'FocalLength':
                            metadata['focal_length'] = self._parse_focal_length(value)
                        elif tag_name == 'DateTimeOriginal':
                            metadata['date_taken'] = self._parse_datetime(value)
                        elif tag_name == 'GPSInfo':
                            gps_data = self._parse_gps(value)
                            metadata.update(gps_data)
                
                return metadata
                
        except Exception as e:
            raise MetadataExtractionError(f"Error reading image EXIF: {str(e)}")
    
    def _parse_gps(self, gps_info: Dict) -> Dict[str, float]:
        """Parse GPS coordinates from EXIF"""
        pass
```

### Thumbnail Generation

```python
class ThumbnailGenerator:
    """Generate thumbnails for media files"""
    
    def __init__(self, thumbnail_dir: Path, size: int = 300):
        self.thumbnail_dir = thumbnail_dir
        self.size = size
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_video_thumbnail(
        self,
        video_path: Path,
        media_item_id: str,
        timestamp: Optional[float] = None
    ) -> Path:
        """
        Generate thumbnail from video at specified timestamp
        
        Args:
            video_path: Path to video file
            media_item_id: UUID of media item
            timestamp: Time in seconds (default: 10% into video)
        
        Returns:
            Path to generated thumbnail
        """
        thumbnail_path = self.thumbnail_dir / f"{media_item_id}.jpg"
        
        if timestamp is None:
            # Get 10% into the video
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['format']['duration'])
            timestamp = duration * 0.1
        
        try:
            # Extract frame at timestamp
            (
                ffmpeg
                .input(str(video_path), ss=timestamp)
                .output(
                    str(thumbnail_path),
                    vframes=1,
                    format='image2',
                    vcodec='mjpeg',
                    s=f"{self.size}x{self.size}",
                    q=2
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            return thumbnail_path
            
        except ffmpeg.Error as e:
            raise ThumbnailGenerationError(f"FFmpeg error: {e.stderr.decode()}")
    
    async def generate_image_thumbnail(
        self,
        image_path: Path,
        media_item_id: str
    ) -> Path:
        """
        Generate thumbnail from image
        """
        thumbnail_path = self.thumbnail_dir / f"{media_item_id}.jpg"
        
        try:
            with Image.open(image_path) as img:
                # Handle orientation
                img = self._correct_orientation(img)
                
                # Resize maintaining aspect ratio
                img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
                
                # Save as JPEG
                img.convert('RGB').save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            raise ThumbnailGenerationError(f"Error creating thumbnail: {str(e)}")
    
    def _correct_orientation(self, img: Image.Image) -> Image.Image:
        """Correct image orientation based on EXIF"""
        pass
```

### Main Metadata Coordinator

```python
class MetadataExtractor:
    """Coordinate metadata extraction across all file types"""
    
    def __init__(self, thumbnail_dir: Path):
        self.video_extractor = VideoMetadataExtractor()
        self.audio_extractor = AudioMetadataExtractor()
        self.image_extractor = ImageMetadataExtractor()
        self.thumbnail_generator = ThumbnailGenerator(thumbnail_dir)
    
    async def extract_all_metadata(
        self,
        media_item: MediaItem
    ) -> MediaMetadata:
        """
        Extract all metadata for a media item
        
        Args:
            media_item: MediaItem database object
        
        Returns:
            MediaMetadata object ready to be saved
        """
        file_path = Path(media_item.file_path)
        
        # Extract based on media type
        if media_item.media_type == MediaType.VIDEO:
            metadata_dict = await self.video_extractor.extract(file_path)
            thumbnail_path = await self.thumbnail_generator.generate_video_thumbnail(
                file_path, str(media_item.id)
            )
        
        elif media_item.media_type == MediaType.AUDIO:
            metadata_dict = await self.audio_extractor.extract(file_path)
            thumbnail_path = None  # Could generate waveform visualization
        
        elif media_item.media_type == MediaType.IMAGE:
            metadata_dict = await self.image_extractor.extract(file_path)
            thumbnail_path = await self.thumbnail_generator.generate_image_thumbnail(
                file_path, str(media_item.id)
            )
        
        else:
            metadata_dict = {}
            thumbnail_path = None
        
        # Create MediaMetadata object
        metadata = MediaMetadata(
            media_item_id=media_item.id,
            **metadata_dict
        )
        
        if thumbnail_path:
            metadata.thumbnail_path = str(thumbnail_path)
        
        return metadata
    
    async def batch_extract(
        self,
        media_items: List[MediaItem],
        progress_callback: Optional[Callable] = None
    ) -> List[MediaMetadata]:
        """Extract metadata for multiple items in parallel"""
        pass
```

## Testing Requirements

Create comprehensive tests in `tests/unit/test_metadata_extraction.py`:

1. **Video Metadata Tests**
   - Extract from MP4, MKV, AVI
   - Handle various codecs
   - Parse subtitle tracks
   - Calculate accurate duration

2. **Audio Metadata Tests**
   - Extract ID3 tags from MP3
   - Read FLAC tags
   - Handle missing tags gracefully
   - Parse various date formats

3. **Image Metadata Tests**
   - Read EXIF from JPEG
   - Extract GPS coordinates
   - Handle images without EXIF
   - Parse camera/lens data

4. **Thumbnail Generation Tests**
   - Generate from video
   - Generate from image
   - Handle orientation
   - Verify file size

## Success Criteria

- [ ] Extract video metadata accurately
- [ ] Extract audio tags completely
- [ ] Read image EXIF data
- [ ] Generate thumbnails efficiently
- [ ] Handle missing/corrupt metadata
- [ ] Async operations don't block
- [ ] Tests pass (90%+ coverage)
- [ ] Process 100 files/minute

---

**GENERATE COMPLETE, PRODUCTION-READY CODE FOR ALL REQUIREMENTS ABOVE**