# Test Fixtures

This directory contains sample media files used for testing.

## Files

The sample media files are generated dynamically by test fixtures in `conftest.py`:

- `sample_video.mp4` - Generated test video (1920x1080, 5 seconds)
- `sample_audio.mp3` - Generated test audio (sine wave, 5 seconds)
- `sample_image.jpg` - Generated test image (1920x1080, blue background)

These files are created on-the-fly during test execution and are not stored in the repository.

## Usage

Tests access these files through pytest fixtures:

```python
def test_example(sample_video_file, sample_audio_file, sample_image_file):
    # Use the file paths
    assert sample_video_file.exists()
```
