"""Efficient file hashing with async and parallel support.

Provides SHA256 hashing with memory-efficient streaming and
parallel processing via ProcessPoolExecutor.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


def _hash_file_worker(file_path: Path, chunk_size: int = 8192) -> str:
    """Worker function for parallel hashing (runs in separate process).
    
    Args:
        file_path: Path to file to hash
        chunk_size: Size of chunks to read (bytes)
        
    Returns:
        SHA256 hash as hex string
        
    Raises:
        OSError: If file cannot be read
    """
    sha256 = hashlib.sha256()
    
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    
    return sha256.hexdigest()


class FileHasher:
    """Efficient file hashing with async support and parallel processing.
    
    Uses ProcessPoolExecutor to offload CPU-intensive hashing to worker
    processes, allowing async operations to continue without blocking.
    
    Example:
        >>> hasher = FileHasher(max_workers=4)
        >>> hash_value = await hasher.hash_file_async(Path("video.mp4"))
        >>> print(f"SHA256: {hash_value}")
    """
    
    CHUNK_SIZE: int = 8192 * 8  # 64KB chunks for better performance
    
    def __init__(self, max_workers: int = 4):
        """Initialize file hasher with process pool.
        
        Args:
            max_workers: Maximum number of worker processes
        """
        self.max_workers = max_workers
        self.executor: Optional[ProcessPoolExecutor] = None
        self._initialize_executor()
    
    def _initialize_executor(self):
        """Lazily initialize the process pool executor."""
        if self.executor is None:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
            logger.debug(
                f"Initialized ProcessPoolExecutor with {self.max_workers} workers"
            )
    
    async def hash_file_async(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[Path, int], None]] = None
    ) -> str:
        """Calculate SHA256 hash asynchronously.
        
        Args:
            file_path: Path to file to hash
            progress_callback: Optional callback(file_path, bytes_read)
            
        Returns:
            SHA256 hash as hex string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
            OSError: For other file access errors
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        try:
            loop = asyncio.get_event_loop()
            hash_value = await loop.run_in_executor(
                self.executor,
                _hash_file_worker,
                file_path,
                self.CHUNK_SIZE
            )
            
            if progress_callback:
                file_size = file_path.stat().st_size
                progress_callback(file_path, file_size)
            
            logger.debug(f"Hashed {file_path.name}: {hash_value[:16]}...")
            return hash_value
            
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            raise
    
    def _hash_file_sync(self, file_path: Path) -> str:
        """Calculate SHA256 hash synchronously (CPU-bound).
        
        Args:
            file_path: Path to file to hash
            
        Returns:
            SHA256 hash as hex string
        """
        return _hash_file_worker(file_path, self.CHUNK_SIZE)
    
    async def hash_multiple_files(
        self,
        file_paths: List[Path],
        progress_callback: Optional[Callable[[Path, str], None]] = None
    ) -> Dict[Path, str]:
        """Hash multiple files in parallel.
        
        Args:
            file_paths: List of file paths to hash
            progress_callback: Optional callback(file_path, hash_value)
            
        Returns:
            Dictionary mapping file paths to their SHA256 hashes
        """
        results: Dict[Path, str] = {}
        
        # Create tasks for all files
        tasks = [
            self.hash_file_async(file_path)
            for file_path in file_paths
        ]
        
        # Execute in parallel
        try:
            hashes = await asyncio.gather(*tasks, return_exceptions=True)
            
            for file_path, hash_result in zip(file_paths, hashes):
                if isinstance(hash_result, Exception):
                    logger.error(
                        f"Failed to hash {file_path}: {hash_result}"
                    )
                    continue
                
                results[file_path] = hash_result
                
                if progress_callback:
                    progress_callback(file_path, hash_result)
        
        except Exception as e:
            logger.error(f"Error in parallel hashing: {e}")
        
        return results
    
    async def verify_hash(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file matches expected hash.
        
        Args:
            file_path: Path to file to verify
            expected_hash: Expected SHA256 hash
            
        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_hash = await self.hash_file_async(file_path)
            return actual_hash.lower() == expected_hash.lower()
        except Exception as e:
            logger.error(f"Hash verification failed for {file_path}: {e}")
            return False
    
    def shutdown(self, wait: bool = True):
        """Shutdown the process pool executor.
        
        Args:
            wait: If True, wait for pending tasks to complete
        """
        if self.executor:
            logger.debug("Shutting down FileHasher executor")
            self.executor.shutdown(wait=wait)
            self.executor = None
    
    def __del__(self):
        """Cleanup executor on deletion."""
        if self.executor:
            self.executor.shutdown(wait=False)


__all__ = ["FileHasher"]
