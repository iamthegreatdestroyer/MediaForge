"""Unit tests for file hashing"""
import pytest
from pathlib import Path
from src.core.hasher import FileHasher


@pytest.mark.asyncio
async def test_hash_file(sample_video_file):
    """Test file hashing"""
    hasher = FileHasher()
    file_hash = await hasher.hash_file_async(sample_video_file)
    
    assert file_hash is not None
    assert isinstance(file_hash, str)
    assert len(file_hash) > 0


@pytest.mark.asyncio
async def test_hash_consistency(sample_video_file):
    """Test that hashing same file produces same hash"""
    hasher = FileHasher()
    
    hash1 = await hasher.hash_file_async(sample_video_file)
    hash2 = await hasher.hash_file_async(sample_video_file)
    
    assert hash1 == hash2


@pytest.mark.asyncio
async def test_different_files_different_hashes(
    sample_video_file,
    sample_audio_file
):
    """Test that different files produce different hashes"""
    hasher = FileHasher()
    
    hash1 = await hasher.hash_file_async(sample_video_file)
    hash2 = await hasher.hash_file_async(sample_audio_file)
    
    assert hash1 != hash2


@pytest.mark.asyncio
async def test_hash_nonexistent_file(tmp_path):
    """Test hashing nonexistent file raises error"""
    hasher = FileHasher()
    nonexistent = tmp_path / "does_not_exist.mp4"
    
    with pytest.raises(FileNotFoundError):
        await hasher.hash_file_async(nonexistent)


@pytest.mark.asyncio
async def test_hash_empty_file(tmp_path):
    """Test hashing empty file"""
    hasher = FileHasher()
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b'')
    
    file_hash = await hasher.hash_file_async(empty_file)
    assert file_hash is not None
    assert len(file_hash) > 0


@pytest.mark.asyncio
async def test_hash_algorithm_format():
    """Test hash format is valid"""
    hasher = FileHasher()
    
    # Create a simple test file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b'test content')
        test_file = Path(f.name)
    
    try:
        file_hash = await hasher.hash_file(test_file)
        
        # Hash should be hex string (SHA-256 = 64 chars)
        assert len(file_hash) == 64
        assert all(c in '0123456789abcdef' for c in file_hash.lower())
    finally:
        test_file.unlink()


@pytest.mark.asyncio
async def test_hash_large_file(tmp_path):
    """Test hashing large file"""
    hasher = FileHasher()
    large_file = tmp_path / "large.bin"
    
    # Create 10MB file
    large_file.write_bytes(b'0' * (10 * 1024 * 1024))
    
    file_hash = await hasher.hash_file(large_file)
    assert file_hash is not None
    assert len(file_hash) == 64
