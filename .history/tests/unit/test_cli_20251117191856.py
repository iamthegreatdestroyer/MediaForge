"""
Unit tests for MediaForge CLI
"""

import pytest
from typer.testing import CliRunner
import asyncio
import os
os.environ["MEDIAFORGE_DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
from src.cli.main import app

runner = CliRunner()

@pytest.mark.asyncio
async def test_scan_command(monkeypatch):
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

@pytest.mark.asyncio
async def test_tag_list_command():
    result = runner.invoke(app, ["tag", "list"])
    assert result.exit_code == 0
    assert "Tags" in result.output

@pytest.mark.asyncio
async def test_collection_list_command():
    result = runner.invoke(app, ["collection", "list"])
    assert result.exit_code == 0
    assert "Collections" in result.output

@pytest.mark.asyncio
async def test_stats_command():
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "Library Statistics" in result.output

@pytest.mark.asyncio
async def test_error_handling(monkeypatch):
    async def fake_scan_directory(self, path, recursive, include_hidden, incremental):
        raise FileNotFoundError("Test error")
    monkeypatch.setattr("src.core.scanner.MediaScanner.scan_directory", fake_scan_directory)
    result = runner.invoke(app, ["scan", "not_a_real_dir", "--no-metadata"])
    assert result.exit_code != 0
    assert "Error" in result.output

@pytest.mark.asyncio
async def test_progress_display(monkeypatch):
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

@pytest.mark.asyncio
async def test_help_text():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "MediaForge" in result.output
    assert "scan" in result.output
    assert "tag" in result.output
    assert "collection" in result.output
