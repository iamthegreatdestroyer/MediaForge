"""Thumbnail generation for video and image files.

Generates preview thumbnails using FFmpeg and PIL.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import ffmpeg
from PIL import Image

logger = logging.getLogger(__name__)


class ThumbnailGenerationError(Exception):
    """Base exception for thumbnail generation errors."""
    pass


class ThumbnailGenerator:
    """Generate thumbnails for media files."""
    
    def __init__(self, thumbnail_dir: Path, size: int = 300):
        """Initialize thumbnail generator.
        
        Args:
            thumbnail_dir: Directory to store thumbnails
            size: Maximum dimension size (thumbnails are square)
        """
        self.thumbnail_dir = Path(thumbnail_dir)
        self.size = size
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Thumbnail generator initialized: {self.thumbnail_dir}")
    
    async def generate_video_thumbnail(
        self,
        video_path: Path,
        media_item_id: str,
        timestamp: Optional[float] = None
    ) -> Path:
        """Generate thumbnail from video at specified timestamp.
        
        Args:
            video_path: Path to video file
            media_item_id: UUID of media item
            timestamp: Time in seconds (default: 10% into video)
            
        Returns:
            Path to generated thumbnail
            
        Raises:
            ThumbnailGenerationError: If generation fails
        """
        thumbnail_path = self.thumbnail_dir / f"{media_item_id}.jpg"
        
        try:
            # Determine timestamp if not provided
            if timestamp is None:
                loop = asyncio.get_event_loop()
                probe = await loop.run_in_executor(
                    None, ffmpeg.probe, str(video_path)
                )
                duration = float(probe['format']['duration'])
                timestamp = duration * 0.1  # 10% into video
            
            # Extract frame at timestamp
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._generate_video_thumbnail_sync,
                video_path,
                thumbnail_path,
                timestamp
            )
            
            logger.debug(f"Generated video thumbnail: {thumbnail_path.name}")
            return thumbnail_path
            
        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if e.stderr else "Unknown error"
            raise ThumbnailGenerationError(f"FFmpeg error: {stderr}")
        except Exception as e:
            raise ThumbnailGenerationError(
                f"Error generating video thumbnail: {str(e)}"
            )
    
    def _generate_video_thumbnail_sync(
        self,
        video_path: Path,
        thumbnail_path: Path,
        timestamp: float
    ) -> None:
        """Synchronous video thumbnail generation (called in executor).
        
        Args:
            video_path: Path to video file
            thumbnail_path: Path for output thumbnail
            timestamp: Time in seconds
        """
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
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
    
    async def generate_image_thumbnail(
        self,
        image_path: Path,
        media_item_id: str
    ) -> Path:
        """Generate thumbnail from image.
        
        Args:
            image_path: Path to image file
            media_item_id: UUID of media item
            
        Returns:
            Path to generated thumbnail
            
        Raises:
            ThumbnailGenerationError: If generation fails
        """
        thumbnail_path = self.thumbnail_dir / f"{media_item_id}.jpg"
        
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._generate_image_thumbnail_sync,
                image_path,
                thumbnail_path
            )
            
            logger.debug(f"Generated image thumbnail: {thumbnail_path.name}")
            return thumbnail_path
            
        except Exception as e:
            raise ThumbnailGenerationError(
                f"Error creating image thumbnail: {str(e)}"
            )
    
    def _generate_image_thumbnail_sync(
        self,
        image_path: Path,
        thumbnail_path: Path
    ) -> None:
        """Synchronous image thumbnail generation (called in executor).
        
        Args:
            image_path: Path to source image
            thumbnail_path: Path for output thumbnail
        """
        with Image.open(image_path) as img:
            # Correct orientation based on EXIF
            img = self._correct_orientation(img)
            
            # Resize maintaining aspect ratio
            img.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
            
            # Convert to RGB and save as JPEG
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
    
    def _correct_orientation(self, img: Image.Image) -> Image.Image:
        """Correct image orientation based on EXIF.
        
        Args:
            img: PIL Image object
            
        Returns:
            Corrected image
        """
        try:
            exif = img.getexif()
            if exif:
                orientation = exif.get(0x0112)  # Orientation tag
                
                if orientation == 2:
                    # Mirrored horizontal
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    # Rotated 180
                    img = img.rotate(180, expand=True)
                elif orientation == 4:
                    # Mirrored vertical
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                elif orientation == 5:
                    # Mirrored horizontal then rotated 90 CCW
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    img = img.rotate(90, expand=True)
                elif orientation == 6:
                    # Rotated 90 CCW
                    img = img.rotate(270, expand=True)
                elif orientation == 7:
                    # Mirrored horizontal then rotated 90 CW
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    # Rotated 90 CW
                    img = img.rotate(90, expand=True)
        except Exception as e:
            logger.debug(f"Could not correct orientation: {e}")
        
        return img
    
    async def generate_thumbnail(
        self,
        file_path: Path,
        media_item_id: str,
        media_type: str,
        timestamp: Optional[float] = None
    ) -> Optional[Path]:
        """Generate thumbnail based on media type.
        
        Args:
            file_path: Path to media file
            media_item_id: UUID of media item
            media_type: Type of media (video/image/audio)
            timestamp: Timestamp for video thumbnails (optional)
            
        Returns:
            Path to thumbnail or None if not applicable
            
        Raises:
            ThumbnailGenerationError: If generation fails
        """
        if media_type == 'video':
            return await self.generate_video_thumbnail(
                file_path, media_item_id, timestamp
            )
        elif media_type == 'image':
            return await self.generate_image_thumbnail(
                file_path, media_item_id
            )
        else:
            # Audio and other types don't get thumbnails yet
            return None
    
    def delete_thumbnail(self, media_item_id: str) -> bool:
        """Delete thumbnail for a media item.
        
        Args:
            media_item_id: UUID of media item
            
        Returns:
            True if deleted, False if not found
        """
        thumbnail_path = self.thumbnail_dir / f"{media_item_id}.jpg"
        
        if thumbnail_path.exists():
            try:
                thumbnail_path.unlink()
                logger.debug(f"Deleted thumbnail: {thumbnail_path.name}")
                return True
            except Exception as e:
                logger.error(f"Could not delete thumbnail: {e}")
                return False
        
        return False
    
    def get_thumbnail_path(self, media_item_id: str) -> Optional[Path]:
        """Get path to thumbnail if it exists.
        
        Args:
            media_item_id: UUID of media item
            
        Returns:
            Path to thumbnail or None
        """
        thumbnail_path = self.thumbnail_dir / f"{media_item_id}.jpg"
        return thumbnail_path if thumbnail_path.exists() else None
