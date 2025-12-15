"""High-performance media scanner with async support and incremental scanning.

Orchestrates file discovery, hashing, and database operations for efficient
media library management.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional, Callable, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Database
from src.core.file_utils import MimeTypeDetector, get_all_files
from src.core.hasher import FileHasher
from src.models.media import MediaItem, MediaType

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Results from a scan operation.
    
    Attributes:
        total_files: Total number of files encountered
        new_files: Number of new files added to database
        updated_files: Number of existing files updated
        skipped_files: Number of files skipped (already in DB)
        error_files: Number of files that encountered errors
        total_size: Total size of all files in bytes
        scan_duration: Time taken for scan in seconds
        errors: List of error messages
    """
    total_files: int = 0
    new_files: int = 0
    updated_files: int = 0
    skipped_files: int = 0
    error_files: int = 0
    total_size: int = 0
    scan_duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    new_file_paths: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """Human-readable summary of scan results."""
        return (
            f"Scan Results:\n"
            f"  Total files: {self.total_files}\n"
            f"  New: {self.new_files}\n"
            f"  Updated: {self.updated_files}\n"
            f"  Skipped: {self.skipped_files}\n"
            f"  Errors: {self.error_files}\n"
            f"  Total size: {self._format_size(self.total_size)}\n"
            f"  Duration: {self.scan_duration:.2f}s"
        )
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class MediaScanner:
    """High-performance media file scanner with incremental support.
    
    Features:
    - Async/await for non-blocking I/O
    - Parallel file hashing via process pool
    - Incremental scanning (skip unchanged files)
    - Progress reporting
    - Comprehensive error handling
    - Batch database operations
    
    Example:
        >>> db = Database("sqlite+aiosqlite:///media.db")
        >>> scanner = MediaScanner(db, max_workers=4)
        >>> result = await scanner.scan_directory(Path("/media"))
        >>> print(result)
    """
    
    PROGRESS_INTERVAL = 100  # Report progress every N files
    BATCH_SIZE = 50  # Batch size for database operations
    
    def __init__(
        self,
        database: Database,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """Initialize media scanner.
        
        Args:
            database: Database instance for storing media items
            max_workers: Number of worker processes for hashing
            progress_callback: Optional callback(processed, total) for progress
        """
        self.db = database
        self.mime_detector = MimeTypeDetector()
        self.hasher = FileHasher(max_workers=max_workers)
        self.progress_callback = progress_callback
    
    async def scan_directory(
        self,
        root_dir: Path,
        recursive: bool = True,
        include_hidden: bool = False,
        incremental: bool = True
    ) -> ScanResult:
        """Scan directory for media files and add to database.
        
        Args:
            root_dir: Root directory to scan
            recursive: Scan subdirectories recursively
            include_hidden: Include hidden files and directories
            incremental: Skip files already in database with matching hash
        
        Returns:
            ScanResult with statistics about the scan
            
        Raises:
            ValueError: If root_dir doesn't exist or isn't a directory
        """
        start_time = time.time()
        result = ScanResult()
        
        logger.info(f"Starting scan of {root_dir}")
        logger.info(
            f"Options: recursive={recursive}, "
            f"include_hidden={include_hidden}, incremental={incremental}"
        )
        
        try:
            # Phase 1: Discovery - find all media files
            logger.info("Phase 1: Discovering files...")
            extensions = self.mime_detector.ALL_MEDIA_EXTENSIONS
            file_paths = get_all_files(
                root_dir,
                recursive=recursive,
                include_hidden=include_hidden,
                extensions=extensions
            )
            
            result.total_files = len(file_paths)
            logger.info(f"Found {result.total_files} media files")
            
            if not file_paths:
                result.scan_duration = time.time() - start_time
                return result
            
            # Phase 2: Process files
            logger.info("Phase 2: Processing files...")
            scan_result = await self._scan_files(file_paths, incremental)
            
            # Merge results
            result.new_files = scan_result.new_files
            result.updated_files = scan_result.updated_files
            result.skipped_files = scan_result.skipped_files
            result.error_files = scan_result.error_files
            result.total_size = scan_result.total_size
            result.errors = scan_result.errors
            result.new_file_paths = scan_result.new_file_paths
            
        except ValueError:
            # Re-raise validation errors (invalid directory, etc.)
            raise
        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            result.errors.append(f"Scan failed: {e}")
        
        result.scan_duration = time.time() - start_time
        logger.info(f"Scan completed in {result.scan_duration:.2f}s")
        logger.info(str(result))
        
        return result
    
    async def _scan_files(
        self,
        file_paths: List[Path],
        incremental: bool
    ) -> ScanResult:
        """Process a list of files.
        
        Args:
            file_paths: List of file paths to process
            incremental: Skip files already in database
            
        Returns:
            ScanResult with processing statistics
        """
        result = ScanResult()
        processed = 0
        
        # Process files in batches
        for i in range(0, len(file_paths), self.BATCH_SIZE):
            batch = file_paths[i:i + self.BATCH_SIZE]
            
            async with self.db.session() as session:
                for file_path in batch:
                    try:
                        is_new, is_updated, error = await self._process_file(
                            file_path, session, incremental
                        )
                        
                        if error:
                            result.error_files += 1
                            result.errors.append(f"{file_path}: {error}")
                        elif is_new:
                            result.new_files += 1
                                result.new_file_paths.append(str(file_path))
                        elif is_updated:
                            result.updated_files += 1
                        else:
                            result.skipped_files += 1
                        
                        # Add to total size
                        try:
                            result.total_size += file_path.stat().st_size
                        except OSError:
                            pass
                        
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        result.error_files += 1
                        result.errors.append(f"{file_path}: {e}")
                    
                    processed += 1
                    
                    # Report progress
                    if processed % self.PROGRESS_INTERVAL == 0:
                        logger.info(f"Processed {processed}/{len(file_paths)} files")
                        if self.progress_callback:
                            self.progress_callback(processed, len(file_paths))
        
        return result
    
    async def _process_file(
        self,
        file_path: Path,
        session: AsyncSession,
        incremental: bool
    ) -> Tuple[bool, bool, Optional[str]]:
        """Process a single file.
        
        Args:
            file_path: Path to file to process
            session: Database session
            incremental: Skip if already in database
            
        Returns:
            Tuple of (is_new, is_updated, error_message)
        """
        try:
            # Get file stats
            stat = file_path.stat()
            file_size = stat.st_size
            file_modified_at = datetime.fromtimestamp(stat.st_mtime, UTC)
            
            # Calculate hash
            file_hash = await self.hasher.hash_file_async(file_path)
            
            # Check if file already exists
            if incremental:
                should_skip = await self._should_skip_file(
                    file_path, file_hash, file_modified_at, session
                )
                if should_skip:
                    return (False, False, None)
            
            # Check for duplicate by hash
            result = await session.execute(
                select(MediaItem).where(MediaItem.file_hash == file_hash)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update if path or modification time changed
                # Make existing timestamp timezone-aware if it isn't
                existing_mtime = existing.file_modified_at
                if existing_mtime and existing_mtime.tzinfo is None:
                    existing_mtime = existing_mtime.replace(tzinfo=UTC)
                
                if (existing.file_path != str(file_path) or
                    existing_mtime != file_modified_at):
                    existing.file_path = str(file_path)
                    existing.file_name = file_path.name
                    existing.file_modified_at = file_modified_at
                    existing.last_scanned_at = datetime.now(UTC)
                    session.add(existing)
                    return (False, True, None)
                else:
                    return (False, False, None)
            
            # Create new media item
            media_item = await self._create_media_item(file_path, file_hash)
            session.add(media_item)
            
            return (True, False, None)
            
        except Exception as e:
            error_msg = f"Failed to process: {e}"
            logger.error(f"{file_path}: {error_msg}")
            return (False, False, error_msg)
    
    async def _should_skip_file(
        self,
        file_path: Path,
        file_hash: str,
        file_modified_at: datetime,
        session: AsyncSession
    ) -> bool:
        """Check if file should be skipped (already in database).
        
        Args:
            file_path: Path to file
            file_hash: SHA256 hash of file
            file_modified_at: File modification timestamp
            session: Database session
            
        Returns:
            True if file should be skipped
        """
        # Check by path first (fastest)
        result = await session.execute(
            select(MediaItem).where(MediaItem.file_path == str(file_path))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Skip if hash and modification time match
            # Make existing timestamp timezone-aware if it isn't
            existing_mtime = existing.file_modified_at
            if existing_mtime and existing_mtime.tzinfo is None:
                existing_mtime = existing_mtime.replace(tzinfo=UTC)
            
            if (existing.file_hash == file_hash and
                existing_mtime == file_modified_at):
                return True
        
        return False
    
    async def _create_media_item(
        self,
        file_path: Path,
        file_hash: str
    ) -> MediaItem:
        """Create MediaItem from file.
        
        Args:
            file_path: Path to file
            file_hash: SHA256 hash of file
            
        Returns:
            New MediaItem instance (not yet added to session)
        """
        stat = file_path.stat()
        mime_type = self.mime_detector.detect_mime_type(file_path)
        media_type_str = self.mime_detector.get_media_type(file_path)
        
        # Convert string media type to enum
        try:
            media_type_enum = MediaType(media_type_str)
        except ValueError:
            media_type_enum = MediaType.other
        
        return MediaItem(
            file_path=str(file_path),
            file_name=file_path.name,
            file_size=stat.st_size,
            file_hash=file_hash,
            mime_type=mime_type,
            media_type=media_type_enum,
            file_created_at=datetime.fromtimestamp(stat.st_ctime, UTC),
            file_modified_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            last_scanned_at=datetime.now(UTC),
            is_processed=False,
            is_compressed=False
        )
    
    async def rescan_modified_files(self) -> ScanResult:
        """Rescan files that have been modified since last scan.
        
        Returns:
            ScanResult with statistics about modified files
        """
        start_time = time.time()
        result = ScanResult()
        
        logger.info("Starting rescan of modified files...")
        
        try:
            async with self.db.session() as session:
                # Get all media items
                db_result = await session.execute(select(MediaItem))
                media_items = db_result.scalars().all()
                
                result.total_files = len(media_items)
                processed = 0
                
                for item in media_items:
                    try:
                        file_path = Path(item.file_path)
                        
                        # Check if file still exists
                        if not file_path.exists():
                            logger.warning(f"File no longer exists: {file_path}")
                            result.error_files += 1
                            continue
                        
                        stat = file_path.stat()
                        current_modified = datetime.fromtimestamp(stat.st_mtime, UTC)
                        
                        # Make existing timestamp timezone-aware if it isn't
                        existing_mtime = item.file_modified_at
                        if existing_mtime and existing_mtime.tzinfo is None:
                            existing_mtime = existing_mtime.replace(tzinfo=UTC)
                        
                        # Check if modified
                        if current_modified > existing_mtime:
                            # Recalculate hash
                            new_hash = await self.hasher.hash_file_async(file_path)
                            
                            if new_hash != item.file_hash:
                                item.file_hash = new_hash
                                item.file_size = stat.st_size
                                item.file_modified_at = current_modified
                                item.last_scanned_at = datetime.now(UTC)
                                item.is_processed = False
                                session.add(item)
                                result.updated_files += 1
                            else:
                                result.skipped_files += 1
                        else:
                            result.skipped_files += 1
                        
                        processed += 1
                        if processed % self.PROGRESS_INTERVAL == 0:
                            logger.info(
                                f"Rescanned {processed}/{result.total_files} files"
                            )
                    
                    except Exception as e:
                        logger.error(f"Error rescanning {item.file_path}: {e}")
                        result.error_files += 1
                        result.errors.append(f"{item.file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Rescan failed: {e}", exc_info=True)
            result.errors.append(f"Rescan failed: {e}")
        
        result.scan_duration = time.time() - start_time
        logger.info(f"Rescan completed in {result.scan_duration:.2f}s")
        logger.info(str(result))
        
        return result
    
    async def verify_file_integrity(self, media_item_id: str) -> bool:
        """Verify file still exists and hash matches.
        
        Args:
            media_item_id: UUID of media item to verify
            
        Returns:
            True if file exists and hash matches, False otherwise
        """
        try:
            async with self.db.session() as session:
                result = await session.execute(
                    select(MediaItem).where(MediaItem.id == media_item_id)
                )
                media_item = result.scalar_one_or_none()
                
                if not media_item:
                    logger.error(f"Media item not found: {media_item_id}")
                    return False
                
                file_path = Path(media_item.file_path)
                
                if not file_path.exists():
                    logger.error(f"File no longer exists: {file_path}")
                    return False
                
                # Verify hash
                return await self.hasher.verify_hash(
                    file_path, media_item.file_hash
                )
        
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'hasher'):
            self.hasher.shutdown(wait=False)


__all__ = ["MediaScanner", "ScanResult"]
