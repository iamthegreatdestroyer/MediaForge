"""Tests for CLI display utilities."""

import pytest
from unittest.mock import MagicMock, patch
from io import StringIO

from src.cli.display import (
    format_file_size,
    display_error,
    display_success,
    display_info,
    display_stats,
    display_table,
    display_scan_results,
)


class TestFormatFileSize:
    """Tests for format_file_size function."""
    
    def test_bytes(self):
        """Test formatting bytes."""
        assert format_file_size(0) == "0.00 B"
        assert format_file_size(512) == "512.00 B"
        assert format_file_size(1023) == "1023.00 B"
    
    def test_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(2048) == "2.00 KB"
        assert format_file_size(1536) == "1.50 KB"
    
    def test_megabytes(self):
        """Test formatting megabytes."""
        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 5) == "5.00 MB"
    
    def test_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_file_size(1024 ** 3) == "1.00 GB"
        assert format_file_size(1024 ** 3 * 2.5) == "2.50 GB"
    
    def test_terabytes(self):
        """Test formatting terabytes."""
        assert format_file_size(1024 ** 4) == "1.00 TB"
    
    def test_petabytes(self):
        """Test formatting petabytes."""
        assert format_file_size(1024 ** 5) == "1.00 PB"


class TestDisplayFunctions:
    """Tests for display functions."""
    
    @pytest.fixture
    def mock_console(self):
        """Mock the Rich console."""
        with patch('src.cli.display.console') as mock:
            yield mock
    
    def test_display_error(self, mock_console):
        """Test display_error function."""
        display_error("Test error message")
        
        mock_console.print.assert_called_once()
        call_args = mock_console.print.call_args
        # Check that a Panel was passed
        assert call_args is not None
    
    def test_display_success(self, mock_console):
        """Test display_success function."""
        display_success("Operation completed")
        
        mock_console.print.assert_called_once()
    
    def test_display_info(self, mock_console):
        """Test display_info function."""
        display_info("Information message")
        
        mock_console.print.assert_called_once()
    
    def test_display_stats(self, mock_console):
        """Test display_stats function."""
        stats = {
            "Total Files": 100,
            "Total Size": "1.5 GB",
            "Videos": 50,
            "Images": 50,
        }
        
        display_stats(stats)
        
        mock_console.print.assert_called_once()
    
    def test_display_table(self, mock_console):
        """Test display_table function."""
        columns = ["Name", "Size", "Type"]
        rows = [
            ["video.mp4", "100 MB", "video"],
            ["image.jpg", "5 MB", "image"],
        ]
        
        display_table("Test Table", columns, rows)
        
        mock_console.print.assert_called_once()


class TestDisplayScanResults:
    """Tests for display_scan_results function."""
    
    @pytest.fixture
    def mock_console(self):
        """Mock the Rich console."""
        with patch('src.cli.display.console') as mock:
            yield mock
    
    def test_display_scan_results_basic(self, mock_console):
        """Test displaying basic scan results."""
        result = MagicMock()
        result.total_files = 100
        result.new_files = 10
        result.updated_files = 5
        result.skipped_files = 85
        result.error_files = 0
        result.total_size = 1024 * 1024 * 500  # 500 MB
        result.scan_duration = 45.5
        result.errors = None
        
        display_scan_results(result)
        
        mock_console.print.assert_called()
    
    def test_display_scan_results_with_errors(self, mock_console):
        """Test displaying scan results with errors."""
        result = MagicMock()
        result.total_files = 100
        result.new_files = 10
        result.updated_files = 5
        result.skipped_files = 80
        result.error_files = 5
        result.total_size = 1024 * 1024 * 500
        result.scan_duration = 45.5
        result.errors = [
            "Error 1: File not found",
            "Error 2: Permission denied",
            "Error 3: Invalid format",
        ]
        
        display_scan_results(result)
        
        # Should have multiple print calls (table + errors)
        assert mock_console.print.call_count >= 2
    
    def test_display_scan_results_many_errors(self, mock_console):
        """Test displaying scan results with more than 10 errors."""
        result = MagicMock()
        result.total_files = 100
        result.new_files = 10
        result.updated_files = 5
        result.skipped_files = 70
        result.error_files = 15
        result.total_size = 1024 * 1024 * 500
        result.scan_duration = 45.5
        result.errors = [f"Error {i}" for i in range(15)]
        
        display_scan_results(result)
        
        # Should show "... and X more errors" message
        assert mock_console.print.call_count >= 3
