"""Pytest configuration and fixtures"""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_media_dir():
    """Create a temporary directory for media files during tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_video_file(temp_media_dir):
    """Create a sample video file for testing"""
    # This will be implemented in testing phase
    pass


@pytest.fixture
def sample_image_file(temp_media_dir):
    """Create a sample image file for testing"""
    # This will be implemented in testing phase
    pass
