"""
Unit tests for MediaForge CLI
"""
import pytest
from typer.testing import CliRunner
import os
os.environ["MEDIAFORGE_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
from src.cli.main import app

runner = CliRunner()

def test_scan_command(monkeypatch):
    async def fake_scan_directory(self, path, recursive, include_hidden, incremental):
        class Result:
            total_files = 10
            new_files = 2
            updated_files = 1
            skipped_files = 7
            error_files = 0
            total_size = 1024 * 1024 * 10
            scan_duration = 1.23
            errors = []
            new_file_paths = ["/media/file1.mp4", "/media/file2.mp3"]
        return Result()
    async def fake_batch_extract(self, media_items, progress_callback=None):
        if progress_callback:
            total = len(media_items)
            for i, _ in enumerate(media_items, 1):
                progress_callback(i, total)
    monkeypatch.setattr("src.core.scanner.MediaScanner.scan_directory", fake_scan_directory)
    monkeypatch.setattr("src.core.metadata_extractor.MetadataExtractor.batch_extract", fake_batch_extract)
    result = runner.invoke(app, ["scan", ".", "--no-metadata"])
    assert result.exit_code == 0
    assert "Scan Results" in result.output

def test_tag_list_command():
    result = runner.invoke(app, ["tag", "list"])
    assert result.exit_code == 0
    assert "Tags" in result.output

def test_collection_list_command():
    result = runner.invoke(app, ["collection", "list"])
    assert result.exit_code == 0
    assert "Collections" in result.output

def test_stats_command():
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "Library Statistics" in result.output

def test_error_handling(monkeypatch):
    async def fake_scan_directory(self, path, recursive, include_hidden, incremental):
        raise FileNotFoundError("Test error")
    monkeypatch.setattr("src.core.scanner.MediaScanner.scan_directory", fake_scan_directory)
    result = runner.invoke(app, ["scan", "not_a_real_dir", "--no-metadata"])
    assert result.exit_code != 0
    assert "Error" in result.output

def test_progress_display(monkeypatch):
    async def fake_scan_directory(self, path, recursive, include_hidden, incremental):
        class Result:
            total_files = 5
            new_files = 1
            updated_files = 1
            skipped_files = 3
            error_files = 0
            total_size = 1024 * 1024 * 5
            scan_duration = 0.5
            errors = []
            new_file_paths = ["/media/file1.mp4"]
        return Result()
    async def fake_batch_extract(self, media_items, progress_callback=None):
        if progress_callback:
            total = len(media_items)
            for i, _ in enumerate(media_items, 1):
                progress_callback(i, total)
    monkeypatch.setattr("src.core.scanner.MediaScanner.scan_directory", fake_scan_directory)
    monkeypatch.setattr("src.core.metadata_extractor.MetadataExtractor.batch_extract", fake_batch_extract)
    result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "Scan Results" in result.output
    assert "Metadata extraction complete" in result.output

def test_help_text():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MediaForge" in result.output
    assert "scan" in result.output
    assert "tag" in result.output
    assert "collection" in result.output

def test_search_command_basic(monkeypatch):
    """Test basic search functionality"""
    from src.models.media import MediaItem, MediaType
    from src.models.metadata import MediaMetadata
    
    async def fake_execute(stmt):
        class FakeResult:
            def all(self):
                # Mock media item and metadata
                class MockMedia:
                    id = 1
                    file_name = "test_video.mp4"
                    media_type = MediaType.video
                class MockMeta:
                    duration = 120.5
                    artist = "Test Artist"
                    album = "Test Album"
                    title = "Test Title"
                return [(MockMedia(), MockMeta())]
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    
    result = runner.invoke(app, ["search", "test"])
    assert result.exit_code == 0
    assert "Searching for" in result.output
    assert "Search Results" in result.output

def test_search_command_with_filters(monkeypatch):
    """Test search with media type filter and limit"""
    from src.models.media import MediaItem, MediaType
    from src.models.metadata import MediaMetadata
    
    async def fake_execute(stmt):
        class FakeResult:
            def all(self):
                class MockMedia:
                    id = 2
                    file_name = "audio_file.mp3"
                    media_type = MediaType.audio
                class MockMeta:
                    duration = 180.0
                    artist = "Artist Name"
                    album = "Album Name"
                    title = "Song Title"
                return [(MockMedia(), MockMeta())]
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    
    result = runner.invoke(app, ["search", "music", "--type", "audio", "--limit", "10"])
    assert result.exit_code == 0
    assert "Searching for" in result.output

def test_search_command_no_results(monkeypatch):
    """Test search when no results found"""
    async def fake_execute(stmt):
        class FakeResult:
            def all(self):
                return []
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    
    result = runner.invoke(app, ["search", "nonexistent"])
    assert result.exit_code == 0
    assert "No results found" in result.output

def test_search_command_invalid_type(monkeypatch):
    """Test search with invalid media type"""
    async def fake_execute(stmt):
        class FakeResult:
            def all(self):
                return []
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    
    result = runner.invoke(app, ["search", "test", "--type", "invalid"])
    assert result.exit_code == 0
    assert "Invalid media type" in result.output

def test_reextract_command_basic(monkeypatch):
    """Test basic re-extraction functionality"""
    from src.models.media import MediaItem, MediaType
    
    call_count = {"extract": 0, "execute": 0}
    
    async def fake_extract_all_metadata(self, item):
        call_count["extract"] += 1
        return {
            "duration": 120.0,
            "width": 1920,
            "height": 1080,
            "title": "Extracted Title"
        }
    
    async def fake_execute(stmt):
        call_count["execute"] += 1
        class FakeResult:
            def scalars(self):
                return self
            def all(self):
                # Mock unprocessed items
                class MockItem:
                    id = 1
                    file_name = "test.mp4"
                    file_path = "/path/to/test.mp4"
                    media_type = MediaType.video
                    is_processed = False
                    media_metadata = None
                if call_count["execute"] == 1:  # First call gets items to process
                    return [MockItem()]
                else:  # Subsequent calls for item refresh
                    return MockItem()
            def scalar_one_or_none(self):
                class MockItem:
                    id = 1
                    file_name = "test.mp4"
                    file_path = "/path/to/test.mp4"
                    media_type = MediaType.video
                    is_processed = False
                    media_metadata = None
                return MockItem()
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
        def add(self, obj):
            pass
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    monkeypatch.setattr("src.core.metadata_extractor.MetadataExtractor.extract_all_metadata", fake_extract_all_metadata)
    
    result = runner.invoke(app, ["reextract"])
    assert result.exit_code == 0
    assert "Re-extracting metadata" in result.output
    assert call_count["extract"] >= 1

def test_reextract_command_with_all_flag(monkeypatch):
    """Test re-extraction with --all flag"""
    from src.models.media import MediaItem, MediaType
    
    async def fake_extract_all_metadata(self, item):
        return {
            "duration": 90.0,
            "artist": "Test Artist"
        }
    
    async def fake_execute(stmt):
        class FakeResult:
            def scalars(self):
                return self
            def all(self):
                class MockItem:
                    id = 2
                    file_name = "audio.mp3"
                    file_path = "/path/to/audio.mp3"
                    media_type = MediaType.audio
                    is_processed = True
                    media_metadata = None
                return [MockItem()]
            def scalar_one_or_none(self):
                class MockItem:
                    id = 2
                    file_name = "audio.mp3"
                    file_path = "/path/to/audio.mp3"
                    media_type = MediaType.audio
                    is_processed = True
                    media_metadata = None
                return MockItem()
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
        def add(self, obj):
            pass
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    monkeypatch.setattr("src.core.metadata_extractor.MetadataExtractor.extract_all_metadata", fake_extract_all_metadata)
    
    result = runner.invoke(app, ["reextract", "--all"])
    assert result.exit_code == 0
    assert "Re-extracting metadata" in result.output

def test_reextract_command_with_limit(monkeypatch):
    """Test re-extraction with --limit"""
    from src.models.media import MediaItem, MediaType
    
    async def fake_extract_all_metadata(self, item):
        return {"duration": 60.0}
    
    async def fake_execute(stmt):
        class FakeResult:
            def scalars(self):
                return self
            def all(self):
                # Return empty to trigger "No items to process"
                return []
            def scalar_one_or_none(self):
                return None
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
        def add(self, obj):
            pass
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    monkeypatch.setattr("src.core.metadata_extractor.MetadataExtractor.extract_all_metadata", fake_extract_all_metadata)
    
    result = runner.invoke(app, ["reextract", "--limit", "5"])
    assert result.exit_code == 0
    assert "No items to process" in result.output

def test_reextract_command_no_items(monkeypatch):
    """Test re-extraction when no items need processing"""
    async def fake_execute(stmt):
        class FakeResult:
            def scalars(self):
                return self
            def all(self):
                return []
        return FakeResult()
    
    class FakeSession:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def execute(self, stmt):
            return await fake_execute(stmt)
    
    class FakeDB:
        def session(self):
            return FakeSession()
        async def create_tables(self):
            pass
    
    def fake_get_db():
        return FakeDB()
    
    monkeypatch.setattr("src.cli.main.get_db", fake_get_db)
    
    result = runner.invoke(app, ["reextract"])
    assert result.exit_code == 0
    assert "No items to process" in result.output
