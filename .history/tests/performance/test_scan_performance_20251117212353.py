"""Performance benchmarks for scanning operations"""
import pytest
import time
from pathlib import Path
from src.core.scanner import MediaScanner
from src.core.hasher import FileHasher


@pytest.mark.asyncio
async def test_scan_performance_small_directory(db, tmp_path):
    """Benchmark scanning a small directory (10 files)"""
    # Create 10 test files
    for i in range(10):
        (tmp_path / f"video{i}.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom' * 100)
    
    scanner = MediaScanner(db)
    
    start_time = time.time()
    result = await scanner.scan_directory(tmp_path)
    duration = time.time() - start_time
    
    assert result.total_files == 10
    assert duration < 5.0  # Should complete in under 5 seconds
    print(f"\n[PERF] Scanned 10 files in {duration:.3f}s ({duration/10:.3f}s per file)")


@pytest.mark.asyncio
async def test_scan_performance_medium_directory(db, tmp_path):
    """Benchmark scanning a medium directory (50 files)"""
    # Create 50 test files
    for i in range(50):
        (tmp_path / f"video{i}.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom' * 100)
    
    scanner = MediaScanner(db)
    
    start_time = time.time()
    result = await scanner.scan_directory(tmp_path)
    duration = time.time() - start_time
    
    assert result.total_files == 50
    assert duration < 30.0  # Should complete in under 30 seconds
    print(f"\n[PERF] Scanned 50 files in {duration:.3f}s ({duration/50:.3f}s per file)")


@pytest.mark.asyncio
async def test_incremental_scan_performance(db, tmp_path):
    """Benchmark incremental scan performance"""
    # Create initial files
    for i in range(20):
        (tmp_path / f"video{i}.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom' * 100)
    
    scanner = MediaScanner(db)
    
    # Initial scan
    start_time = time.time()
    result1 = await scanner.scan_directory(tmp_path, incremental=True)
    initial_duration = time.time() - start_time
    
    # Add 5 more files
    for i in range(20, 25):
        (tmp_path / f"video{i}.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom' * 100)
    
    # Incremental scan
    start_time = time.time()
    result2 = await scanner.scan_directory(tmp_path, incremental=True)
    incremental_duration = time.time() - start_time
    
    assert result1.new_files == 20
    assert result2.new_files == 5
    assert result2.skipped_files == 20
    
    # Incremental should be faster than rescanning all
    print(f"\n[PERF] Initial scan: {initial_duration:.3f}s")
    print(f"[PERF] Incremental scan: {incremental_duration:.3f}s")
    print(f"[PERF] Speedup: {initial_duration/incremental_duration:.2f}x")


@pytest.mark.asyncio
async def test_hash_performance(tmp_path):
    """Benchmark file hashing performance"""
    # Create files of different sizes
    sizes = [
        (1, "1MB"),
        (10, "10MB"),
        (50, "50MB")
    ]
    
    hasher = FileHasher()
    results = []
    
    for size_mb, label in sizes:
        test_file = tmp_path / f"test_{label}.bin"
        test_file.write_bytes(b'0' * (size_mb * 1024 * 1024))
        
        start_time = time.time()
        await hasher.hash_file_async(test_file)
        duration = time.time() - start_time
        
        throughput = size_mb / duration if duration > 0 else 0
        results.append((label, duration, throughput))
        print(f"\n[PERF] Hashed {label} file in {duration:.3f}s ({throughput:.2f} MB/s)")
    
    # Verify hashing is reasonably fast
    assert all(duration < 10 for _, duration, _ in results)


@pytest.mark.asyncio
async def test_recursive_scan_performance(db, tmp_path):
    """Benchmark recursive directory scanning"""
    # Create nested structure: 5 levels, 5 files per level
    def create_nested(parent: Path, depth: int, max_depth: int = 5):
        if depth >= max_depth:
            return
        
        for i in range(5):
            (parent / f"file{depth}_{i}.mp4").write_bytes(
                b'\x00\x00\x00\x20ftypisom' * 100
            )
        
        if depth < max_depth - 1:
            subdir = parent / f"level{depth}"
            subdir.mkdir()
            create_nested(subdir, depth + 1, max_depth)
    
    create_nested(tmp_path, 0)
    
    scanner = MediaScanner(db)
    
    start_time = time.time()
    result = await scanner.scan_directory(tmp_path, recursive=True)
    duration = time.time() - start_time
    
    assert result.total_files == 25  # 5 files × 5 levels
    print(f"\n[PERF] Recursive scan of 25 files in 5 levels: {duration:.3f}s")


@pytest.mark.asyncio
async def test_database_insertion_performance(db, tmp_path):
    """Benchmark database insertion speed"""
    from src.models.media import MediaItem, MediaType
    
    # Create test files
    num_files = 100
    for i in range(num_files):
        (tmp_path / f"video{i}.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom')
    
    scanner = MediaScanner(db)
    
    start_time = time.time()
    result = await scanner.scan_directory(tmp_path)
    duration = time.time() - start_time
    
    assert result.total_files == num_files
    
    insertions_per_second = num_files / duration if duration > 0 else 0
    print(f"\n[PERF] Inserted {num_files} records in {duration:.3f}s ({insertions_per_second:.2f} records/s)")


@pytest.mark.asyncio
async def test_mixed_media_type_performance(db, tmp_path):
    """Benchmark scanning mixed media types"""
    # Create mixed media files
    for i in range(10):
        (tmp_path / f"video{i}.mp4").write_bytes(b'\x00\x00\x00\x20ftypisom' * 100)
        (tmp_path / f"audio{i}.mp3").write_bytes(b'\xff\xfb\x90\x00' + b'\x00' * 100)
        (tmp_path / f"image{i}.jpg").write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
    
    scanner = MediaScanner(db)
    
    start_time = time.time()
    result = await scanner.scan_directory(tmp_path)
    duration = time.time() - start_time
    
    assert result.total_files == 30
    print(f"\n[PERF] Scanned 30 mixed media files in {duration:.3f}s")
