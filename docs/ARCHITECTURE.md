# MediaForge Architecture

## System Overview

MediaForge is a comprehensive media library management system built with Python 3.11+, leveraging async/await patterns, Docker containerization, and AI-assisted development through GitHub Copilot.

## Core Principles

1. **Async-First**: All I/O operations use async/await for maximum concurrency
2. **Type-Safe**: Complete type hints throughout the codebase
3. **Testable**: High test coverage with comprehensive fixtures
4. **Scalable**: Designed to handle millions of media items
5. **Extensible**: Modular architecture for easy feature additions

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Database**: SQLite with SQLAlchemy 2.0 ORM
- **Media Processing**: FFmpeg (via ffmpeg-python)
- **Image Processing**: Pillow
- **Audio Metadata**: Mutagen
- **Async Framework**: asyncio

### Frontend (Phase 2)
- **API**: FastAPI
- **Web UI**: React (future)
- **CLI**: Typer + Rich

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Database Migrations**: Alembic
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: Black, Flake8, Mypy

## Architecture Layers

### 1. Data Layer (`src/models/`)

Database models and schemas:

```
MediaItem (Primary Entity)
  ├── MediaMetadata (1:1)
  ├── Tags (M:N)
  └── Collections (M:N)
```

**Key Entities:**
- `MediaItem`: Core media file representation
- `MediaMetadata`: Rich metadata (video, audio, image)
- `Tag`: Categorization labels
- `Collection`: Logical groupings

### 2. Core Engine (`src/core/`)

Business logic and processing:

**Components:**
- `scanner.py`: File discovery and cataloging
- `hasher.py`: SHA256 file hashing
- `metadata_extractor.py`: Metadata extraction
- `thumbnail_generator.py`: Preview generation
- `database.py`: Database engine and session management
- `config.py`: Configuration management

### 3. Interface Layer

**CLI (`src/cli/`):**
- Command-line interface using Typer
- Rich terminal output
- Interactive prompts

**API (`src/api/`)** (Phase 2):
- FastAPI REST interface
- WebSocket support for real-time updates
- Authentication and authorization

### 4. Testing Layer (`tests/`)

- **Unit Tests**: Individual component testing
- **Integration Tests**: Workflow testing
- **Performance Tests**: Benchmarking
- **Fixtures**: Reusable test data

## Data Flow

### Media Scanning Workflow

```
1. User initiates scan
   ↓
2. Scanner discovers files
   ↓
3. Hasher calculates SHA256
   ↓
4. Check for duplicates
   ↓
5. Create MediaItem entry
   ↓
6. Extract metadata (async)
   ↓
7. Generate thumbnail (async)
   ↓
8. Save to database
   ↓
9. Return results
```

### Metadata Extraction Pipeline

```
MediaItem
  │
  ├── Video? → FFmpeg extraction → Thumbnail generation
  ├── Audio? → Mutagen extraction → Waveform (optional)
  ├── Image? → EXIF extraction → Thumbnail generation
  └── Save MediaMetadata
```

## Database Schema

### Primary Tables

**media_items**
```sql
CREATE TABLE media_items (
    id UUID PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,
    mime_type TEXT NOT NULL,
    media_type TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    modified_at TIMESTAMP NOT NULL,
    is_processed BOOLEAN DEFAULT FALSE
);
```

**media_metadata**
```sql
CREATE TABLE media_metadata (
    id UUID PRIMARY KEY,
    media_item_id UUID REFERENCES media_items(id),
    -- Video fields
    duration REAL,
    width INTEGER,
    height INTEGER,
    fps REAL,
    -- Audio fields
    artist TEXT,
    album TEXT,
    title TEXT,
    -- Image fields
    camera_make TEXT,
    -- JSON for extensibility
    extra_metadata JSON
);
```

### Indexes

Critical indexes for performance:
- `idx_file_path`: Fast lookup by path
- `idx_file_hash`: Duplicate detection
- `idx_media_type`: Type-based filtering
- `idx_created_at`: Chronological sorting
- `idx_artist_album_title`: Audio library queries

## Async Architecture

### Concurrency Patterns

**I/O-Bound Operations (asyncio):**
- Database queries
- File system operations
- Metadata extraction

**CPU-Bound Operations (ProcessPoolExecutor):**
- File hashing
- Video transcoding (future)
- Image processing

**Example Pattern:**
```python
async def process_files(files: List[Path]) -> List[MediaItem]:
    # Parallel hashing (CPU-bound)
    hashes = await hasher.hash_multiple_files(files)
    
    # Parallel metadata extraction (I/O-bound)
    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(extract_metadata(f))
            for f in files
        ]
    
    return results
```

## Performance Considerations

### Optimization Strategies

1. **Batch Operations**
   - Bulk inserts for database
   - Parallel processing for I/O
   - Connection pooling

2. **Caching**
   - Thumbnail cache
   - Metadata cache
   - Query result cache

3. **Lazy Loading**
   - Load metadata on-demand
   - Paginated results
   - Streaming for large datasets

### Scalability Targets

- **Files**: 1M+ media items
- **Scanning**: 10,000 files/minute on SSD
- **Search**: Sub-second response for most queries
- **Metadata**: <1s extraction per file

## Security Considerations

### Current Phase
- Input validation on all paths
- SQL injection prevention (SQLAlchemy ORM)
- File system sandboxing

### Future Phases
- User authentication
- API token management
- Rate limiting
- Encryption at rest

## Extensibility

### Adding New Media Types

1. Extend `MediaType` enum
2. Create type-specific extractor
3. Add to `MetadataExtractor` coordinator
4. Update thumbnail generator
5. Add tests

### Plugin System (Future)

Planned architecture for plugins:
```python
class MediaForgePlugin:
    def on_scan_complete(self, items: List[MediaItem]):
        pass
    
    def on_metadata_extracted(self, metadata: MediaMetadata):
        pass
```

## Monitoring and Logging

### Logging Strategy

- **DEBUG**: Detailed execution flow
- **INFO**: Key operations and results
- **WARNING**: Non-critical issues
- **ERROR**: Operation failures
- **CRITICAL**: System failures

### Metrics (Future)

- Scan performance
- Database query times
- API response times
- Error rates

## Development Workflow

### AI-Assisted Development

1. **Prompt Design**: Comprehensive specifications in `prompts/`
2. **Code Generation**: GitHub Copilot creates implementation
3. **Review**: Manual code review and refinement
4. **Testing**: Comprehensive test execution
5. **Integration**: Merge into main codebase

### Quality Gates

- All tests must pass
- Code coverage >90%
- No mypy errors
- No flake8 warnings
- Black formatting applied

## Future Roadmap

### Phase 2: Core Features
- Full-text search engine
- FastAPI web interface
- Advanced filtering

### Phase 3: Advanced Features
- Torrent integration
- Compression pipeline
- Device discovery

### Phase 4: Polish
- React web UI
- Mobile apps
- Cloud sync
- AI-powered organization

---

This architecture provides a solid foundation for building a comprehensive, scalable media library system while maintaining code quality and developer productivity through AI assistance.