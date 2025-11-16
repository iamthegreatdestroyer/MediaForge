# Prompt 02: Media Scanner Implementation

## Metadata
- **Phase**: Foundation
- **Priority**: Critical
- **Estimated Time**: 3-4 hours
- **Dependencies**: Prompt 01 (Database Schema)
- **Files to Create**: `src/core/scanner.py`, `src/core/file_utils.py`, `src/core/hasher.py`

---

# GITHUB COPILOT PROMPT: MEDIA SCANNER IMPLEMENTATION

## Context

You are implementing a high-performance, asynchronous media scanner for MediaForge that can:
- Recursively scan directories for media files
- Identify file types using magic bytes and extensions
- Calculate SHA256 hashes for deduplication
- Track file modifications
- Handle large directory trees efficiently
- Support incremental scanning
- Detect and skip already-scanned files

## Technical Requirements

### Core Components

1. **FileScanner**: Main scanning orchestrator
2. **FileHasher**: Efficient file hashing
3. **MimeTypeDetector**: Accurate file type detection
4. **ScanProgress**: Progress tracking and reporting

### Supported Media Types

The scanner must detect and categorize:

**Video**: mp4, mkv, avi, mov, wmv, flv, webm, m4v, mpg, mpeg, 3gp, ogv
**Audio**: mp3, flac, wav, aac, ogg, m4a, wma, opus, ape, alac
**Images**: jpg, jpeg, png, gif, bmp, webp, svg, tiff, tif, heic, raw, cr2, nef
**Documents**: pdf, epub, mobi, azw3, djvu, cbr, cbz
**Streaming**: m3u8, m3u, pls, strm

### Performance Requirements

- Scan 10,000+ files per minute on SSD
- Async I/O for non-blocking operations
- Parallel processing using multiprocessing for CPU-intensive tasks
- Memory-efficient streaming for large files
- Progress reporting every 100 files
- Graceful handling of permission errors

## Implementation Instructions

### Step 1: Create File Utilities (`src/core/file_utils.py`)

```python
from pathlib import Path
from typing import List, Set, Optional
import mimetypes
import magic
from enum import Enum

class MediaType(str, Enum):
    """Media type classification"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    STREAMING = "streaming"
    OTHER = "other"

class MimeTypeDetector:
    """Detect MIME types using magic bytes and file extensions"""
    
    # Define extension to media type mappings
    VIDEO_EXTENSIONS: Set[str] = {".mp4", ".mkv", ".avi", ...}
    AUDIO_EXTENSIONS: Set[str] = {".mp3", ".flac", ".wav", ...}
    # ... etc
    
    def __init__(self):
        self.magic = magic.Magic(mime=True)
    
    def detect_mime_type(self, file_path: Path) -> str:
        """Detect MIME type using magic bytes"""
        pass
    
    def get_media_type(self, file_path: Path) -> MediaType:
        """Classify file into media type category"""
        pass
    
    def is_media_file(self, file_path: Path) -> bool:
        """Check if file is a supported media type"""
        pass

def get_all_files(
    root_dir: Path,
    recursive: bool = True,
    include_hidden: bool = False,
    extensions: Optional[Set[str]] = None
) -> List[Path]:
    """Get all files in directory matching criteria"""
    pass

def is_hidden(file_path: Path) -> bool:
    """Check if file or any parent directory is hidden"""
    pass

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    pass
```

Implement with:
- Efficient file traversal
- Proper error handling for permission denied
- Cross-platform hidden file detection
- MIME type detection with fallback to extension

### Step 2: Create File Hasher (`src/core/hasher.py`)

```python
import hashlib
from pathlib import Path
from typing import BinaryIO
import asyncio
from concurrent.futures import ProcessPoolExecutor

class FileHasher:
    """Efficient file hashing with async support"""
    
    CHUNK_SIZE: int = 8192  # Read in 8KB chunks
    
    def __init__(self, max_workers: int = 4):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
    
    async def hash_file_async(self, file_path: Path) -> str:
        """Calculate SHA256 hash asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._hash_file_sync,
            file_path
        )
    
    def _hash_file_sync(self, file_path: Path) -> str:
        """Calculate SHA256 hash synchronously (CPU-bound)"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(self.CHUNK_SIZE):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    async def hash_multiple_files(self, file_paths: List[Path]) -> Dict[Path, str]:
        """Hash multiple files in parallel"""
        pass
    
    def __del__(self):
        self.executor.shutdown(wait=False)
```

Implement with:
- Memory-efficient streaming
- Parallel processing
- Error handling for large files
- Progress callback support

### Step 3: Create Main Scanner (`src/core/scanner.py`)

```python
from pathlib import Path
from typing import List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from rich.progress import Progress, TaskID

from src.models.media import MediaItem, MediaMetadata
from src.core.file_utils import MimeTypeDetector, MediaType, get_all_files
from src.core.hasher import FileHasher
from src.core.database import Database

@dataclass
class ScanResult:
    """Results from a scan operation"""
    total_files: int = 0
    new_files: int = 0
    updated_files: int = 0
    skipped_files: int = 0
    error_files: int = 0
    total_size: int = 0
    scan_duration: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class MediaScanner:
    """High-performance media file scanner"""
    
    def __init__(
        self,
        database: Database,
        max_workers: int = 4,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
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
        """
        Scan directory for media files and add to database
        
        Args:
            root_dir: Root directory to scan
            recursive: Scan subdirectories
            include_hidden: Include hidden files
            incremental: Skip already-scanned files
        
        Returns:
            ScanResult with statistics
        """
        pass
    
    async def _scan_files(
        self,
        file_paths: List[Path],
        incremental: bool
    ) -> ScanResult:
        """Process a list of files"""
        pass
    
    async def _process_file(
        self,
        file_path: Path,
        session: AsyncSession,
        incremental: bool
    ) -> tuple[bool, bool, Optional[str]]:
        """
        Process a single file
        
        Returns:
            (is_new, is_updated, error_message)
        """
        pass
    
    async def _should_skip_file(
        self,
        file_path: Path,
        file_hash: str,
        session: AsyncSession
    ) -> bool:
        """Check if file should be skipped (already in database)"""
        pass
    
    async def _create_media_item(
        self,
        file_path: Path,
        file_hash: str
    ) -> MediaItem:
        """Create MediaItem from file"""
        pass
    
    async def rescan_modified_files(self) -> ScanResult:
        """Rescan files that have been modified since last scan"""
        pass
    
    async def verify_file_integrity(self, media_item_id: str) -> bool:
        """Verify file still exists and hash matches"""
        pass
```

Implement with:
- Async/await throughout
- Batch database operations
- Progress reporting
- Comprehensive error handling
- Transaction management
- Duplicate detection via hash

### Step 4: Scanning Logic

The scanning process should:

1. **Discovery Phase**
   - Traverse directory tree
   - Filter by extensions
   - Respect hidden file settings
   - Collect all candidate files

2. **Hashing Phase**
   - Calculate SHA256 hashes in parallel
   - Use process pool for CPU-intensive work
   - Report progress every 100 files

3. **Database Phase**
   - Check for existing entries by hash
   - Create new MediaItem entries
   - Update modified files
   - Batch insert for performance

4. **Verification Phase**
   - Validate all operations succeeded
   - Report statistics
   - Log errors

## Testing Requirements

Create `tests/unit/test_scanner.py` with:

1. **Test File Detection**
   - Detect all supported media types
   - Classify files correctly
   - Handle unknown types

2. **Test Hashing**
   - Calculate correct SHA256 hashes
   - Handle large files (>1GB)
   - Parallel hashing performance

3. **Test Scanning**
   - Scan directory with various file types
   - Recursive vs non-recursive
   - Hidden file handling
   - Incremental scanning

4. **Test Database Integration**
   - Create new entries
   - Skip duplicates
   - Update modified files
   - Handle errors gracefully

5. **Test Performance**
   - Scan 1000+ files efficiently
   - Memory usage stays reasonable
   - Progress reporting works

Create `tests/integration/test_scanner_integration.py` for end-to-end tests.

## Success Criteria

- [ ] Scanner detects all supported file types
- [ ] SHA256 hashing is accurate and efficient
- [ ] Async operations don't block
- [ ] Duplicate files are detected
- [ ] Incremental scanning works
- [ ] Progress reporting functional
- [ ] Error handling robust
- [ ] Tests pass (90%+ coverage)
- [ ] Can scan 10,000 files in <1 minute
- [ ] No memory leaks during long scans

## Code Quality Standards

- Full type hints on all functions
- Async/await used correctly
- Proper resource cleanup
- Comprehensive docstrings
- Error messages are informative
- Logging for debugging
- Progress bars using rich

## Example Usage

```python
from pathlib import Path
from src.core.scanner import MediaScanner
from src.core.database import Database

# Initialize
db = Database("sqlite+aiosqlite:///data/mediaforge.db")
scanner = MediaScanner(db, max_workers=4)

# Scan directory
result = await scanner.scan_directory(
    Path("/media_library"),
    recursive=True,
    incremental=True
)

print(f"Scanned {result.total_files} files")
print(f"Added {result.new_files} new files")
print(f"Updated {result.updated_files} files")
```

---

**GENERATE COMPLETE, PRODUCTION-READY CODE FOR ALL REQUIREMENTS ABOVE**