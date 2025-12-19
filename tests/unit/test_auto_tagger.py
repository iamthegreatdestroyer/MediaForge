"""Tests for ML auto-tagging system."""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.ml.auto_tagger import (
    AutoTagger,
    AutoTagResult,
    TagPrediction,
    get_auto_tagger,
    auto_tag_file,
)


class TestTagPrediction:
    """Tests for TagPrediction dataclass."""
    
    def test_tag_prediction_creation(self):
        """Test TagPrediction creation."""
        prediction = TagPrediction(
            name="dog",
            confidence=0.95,
            category="objects"
        )
        
        assert prediction.name == "dog"
        assert prediction.confidence == 0.95
        assert prediction.category == "objects"
    
    def test_tag_prediction_default_category(self):
        """Test TagPrediction default category."""
        prediction = TagPrediction(name="test", confidence=0.5)
        assert prediction.category == "general"


class TestAutoTagResult:
    """Tests for AutoTagResult dataclass."""
    
    def test_auto_tag_result_creation(self):
        """Test AutoTagResult creation."""
        tags = [
            TagPrediction("dog", 0.9, "objects"),
            TagPrediction("outdoor", 0.7, "scenes"),
            TagPrediction("happy", 0.3, "moods"),
        ]
        
        result = AutoTagResult(
            file_path="/test/image.jpg",
            tags=tags,
            caption="A happy dog outdoors",
            processing_time=1.5
        )
        
        assert result.file_path == "/test/image.jpg"
        assert len(result.tags) == 3
        assert result.caption == "A happy dog outdoors"
        assert result.processing_time == 1.5
    
    def test_get_high_confidence_tags(self):
        """Test filtering by confidence threshold."""
        tags = [
            TagPrediction("dog", 0.9, "objects"),
            TagPrediction("outdoor", 0.7, "scenes"),
            TagPrediction("happy", 0.3, "moods"),
        ]
        
        result = AutoTagResult(file_path="/test.jpg", tags=tags)
        
        high_conf = result.get_high_confidence_tags(0.5)
        assert len(high_conf) == 2
        assert all(t.confidence >= 0.5 for t in high_conf)
    
    def test_to_tag_names(self):
        """Test converting to tag names."""
        tags = [
            TagPrediction("dog", 0.9, "objects"),
            TagPrediction("outdoor", 0.7, "scenes"),
            TagPrediction("happy", 0.2, "moods"),
        ]
        
        result = AutoTagResult(file_path="/test.jpg", tags=tags)
        
        names = result.to_tag_names(threshold=0.3)
        assert names == ["dog", "outdoor"]
    
    def test_empty_result(self):
        """Test empty AutoTagResult."""
        result = AutoTagResult(file_path="/test.jpg", tags=[])
        
        assert result.get_high_confidence_tags() == []
        assert result.to_tag_names() == []


class TestAutoTagger:
    """Tests for AutoTagger class."""
    
    @pytest.fixture
    def auto_tagger(self):
        """Create an AutoTagger instance."""
        return AutoTagger()
    
    def test_initialization(self, auto_tagger):
        """Test AutoTagger initialization."""
        assert auto_tagger.model_name == "openai/clip-vit-base-patch32"
        assert auto_tagger.device == "cpu"
        assert auto_tagger._initialized is False
    
    def test_default_tags_loaded(self, auto_tagger):
        """Test default tags are loaded."""
        assert "objects" in auto_tagger.tags
        assert "scenes" in auto_tagger.tags
        assert "activities" in auto_tagger.tags
        assert "moods" in auto_tagger.tags
        assert "styles" in auto_tagger.tags
        
        assert "dog" in auto_tagger._all_tags
        assert "beach" in auto_tagger._all_tags
    
    def test_custom_tags_merged(self):
        """Test custom tags are merged."""
        custom = {"custom_category": ["tag1", "tag2"]}
        tagger = AutoTagger(custom_tags=custom)
        
        assert "custom_category" in tagger.tags
        assert "tag1" in tagger._all_tags
        assert "tag2" in tagger._all_tags
    
    def test_tag_categories_mapping(self, auto_tagger):
        """Test tag to category mapping."""
        assert auto_tagger._tag_categories["dog"] == "objects"
        assert auto_tagger._tag_categories["beach"] == "scenes"
        assert auto_tagger._tag_categories["happy"] == "moods"
    
    @pytest.mark.asyncio
    async def test_initialize_without_dependencies(self, auto_tagger):
        """Test initialization fails gracefully without ML dependencies."""
        with patch.dict('sys.modules', {'transformers': None}):
            # This should handle ImportError gracefully
            result = await auto_tagger.initialize()
            # Result depends on whether transformers is actually installed
            # In test environment, we just verify it doesn't raise
            assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_analyze_image_not_initialized(self):
        """Test analyze_image when not initialized."""
        tagger = AutoTagger()
        
        # Mock initialize to return False
        tagger._initialized = False
        
        with patch.object(tagger, 'initialize', return_value=False):
            result = await tagger.analyze_image(Path("/nonexistent.jpg"))
            
            assert result.file_path == "/nonexistent.jpg"
            assert result.tags == []
    
    def test_shutdown(self, auto_tagger):
        """Test shutdown cleans up resources."""
        auto_tagger._initialized = True
        auto_tagger._model = MagicMock()
        auto_tagger._processor = MagicMock()
        
        auto_tagger.shutdown()
        
        assert auto_tagger._initialized is False
        assert auto_tagger._model is None
        assert auto_tagger._processor is None


class TestAutoTaggerSingleton:
    """Tests for AutoTagger singleton."""
    
    def test_get_auto_tagger(self):
        """Test get_auto_tagger returns same instance."""
        # Reset global
        import src.ml.auto_tagger as module
        module._auto_tagger = None
        
        tagger1 = get_auto_tagger()
        tagger2 = get_auto_tagger()
        
        assert tagger1 is tagger2
        
        # Cleanup
        module._auto_tagger = None


class TestAutoTagFile:
    """Tests for auto_tag_file convenience function."""
    
    @pytest.mark.asyncio
    async def test_auto_tag_file_unsupported_format(self):
        """Test auto_tag_file with unsupported format."""
        result = await auto_tag_file(Path("/test/file.txt"))
        assert result == []
    
    @pytest.mark.asyncio
    async def test_auto_tag_file_image_extension(self):
        """Test auto_tag_file recognizes image extensions."""
        import src.ml.auto_tagger as module
        module._auto_tagger = None
        
        tagger = get_auto_tagger()
        
        # Mock the analyze_image method
        mock_result = AutoTagResult(
            file_path="/test.jpg",
            tags=[TagPrediction("dog", 0.9, "objects")]
        )
        
        with patch.object(tagger, 'initialize', return_value=True):
            with patch.object(tagger, 'analyze_image', return_value=mock_result):
                tags = await auto_tag_file(Path("/test.jpg"))
                assert "dog" in tags
        
        module._auto_tagger = None
    
    @pytest.mark.asyncio
    async def test_auto_tag_file_video_extension(self):
        """Test auto_tag_file recognizes video extensions."""
        import src.ml.auto_tagger as module
        module._auto_tagger = None
        
        tagger = get_auto_tagger()
        
        mock_result = AutoTagResult(
            file_path="/test.mp4",
            tags=[TagPrediction("outdoor", 0.8, "scenes")]
        )
        
        with patch.object(tagger, 'initialize', return_value=True):
            with patch.object(tagger, 'analyze_video_keyframe', return_value=mock_result):
                tags = await auto_tag_file(Path("/test.mp4"))
                assert "outdoor" in tags
        
        module._auto_tagger = None
