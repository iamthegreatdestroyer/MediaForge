"""ML module for MediaForge.

Provides AI-powered features including auto-tagging, visual similarity,
and content understanding.
"""

from src.ml.auto_tagger import (
    AutoTagger,
    AutoTagResult,
    TagPrediction,
    get_auto_tagger,
    auto_tag_file,
)

__all__ = [
    "AutoTagger",
    "AutoTagResult",
    "TagPrediction",
    "get_auto_tagger",
    "auto_tag_file",
]
    """A predicted tag with confidence score.
    
    Attributes:
        name: Tag name
        confidence: Confidence score (0.0 to 1.0)
        category: Tag category (object, scene, action, etc.)
    """
    name: str
    confidence: float
    category: str = "general"


@dataclass
class AutoTagResult:
    """Result of auto-tagging analysis.
    
    Attributes:
        file_path: Path to analyzed file
        tags: List of predicted tags
        caption: Generated caption/description
        embeddings: Raw embeddings (optional)
        processing_time: Time taken in seconds
    """
    file_path: str
    tags: List[TagPrediction]
    caption: str = ""
    embeddings: Optional[List[float]] = None
    processing_time: float = 0.0
    
    def get_high_confidence_tags(
        self,
        threshold: float = 0.5
    ) -> List[TagPrediction]:
        """Get tags above confidence threshold."""
        return [t for t in self.tags if t.confidence >= threshold]
    
    def to_tag_names(self, threshold: float = 0.3) -> List[str]:
        """Get tag names above threshold."""
        return [t.name for t in self.tags if t.confidence >= threshold]


class AutoTagger:
    """ML-powered auto-tagging engine using CLIP.
    
    Uses OpenAI CLIP (Contrastive Language-Image Pre-Training) for:
    - Zero-shot image classification
    - Visual concept detection
    - Content-aware tagging
    
    Example:
        >>> tagger = AutoTagger()
        >>> await tagger.initialize()
        >>> result = await tagger.analyze_image(Path("photo.jpg"))
        >>> print(result.tags)
    """
    
    # Default tag categories for zero-shot classification
    DEFAULT_TAGS: Dict[str, List[str]] = {
        "objects": [
            "person", "face", "animal", "dog", "cat", "bird", "car", "vehicle",
            "building", "house", "tree", "flower", "food", "drink", "book",
            "phone", "computer", "furniture", "clothing", "sports equipment",
        ],
        "scenes": [
            "indoor", "outdoor", "beach", "mountain", "forest", "city",
            "countryside", "sunset", "sunrise", "night", "underwater",
            "aerial view", "landscape", "portrait", "closeup",
        ],
        "activities": [
            "walking", "running", "sitting", "standing", "eating", "drinking",
            "playing", "working", "sleeping", "reading", "traveling",
            "celebrating", "sports", "dancing", "swimming",
        ],
        "moods": [
            "happy", "sad", "peaceful", "exciting", "romantic", "nostalgic",
            "dramatic", "minimalist", "colorful", "dark", "bright",
        ],
        "styles": [
            "professional", "casual", "vintage", "modern", "artistic",
            "documentary", "candid", "posed", "selfie", "group photo",
        ],
    }
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        device: str = "cpu",
        custom_tags: Optional[Dict[str, List[str]]] = None,
    ):
        """Initialize the auto-tagger.
        
        Args:
            model_name: CLIP model to use (HuggingFace model ID)
            device: Device to run on ('cpu' or 'cuda')
            custom_tags: Additional custom tags by category
        """
        self.model_name = model_name
        self.device = device
        self.custom_tags = custom_tags or {}
        
        self._model = None
        self._processor = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = False
        
        # Merge default and custom tags
        self.tags = {**self.DEFAULT_TAGS}
        for category, tag_list in self.custom_tags.items():
            if category in self.tags:
                self.tags[category].extend(tag_list)
            else:
                self.tags[category] = tag_list
        
        # Flatten all tags for batch processing
        self._all_tags = []
        self._tag_categories = {}
        for category, tag_list in self.tags.items():
            for tag in tag_list:
                if tag not in self._tag_categories:
                    self._all_tags.append(tag)
                    self._tag_categories[tag] = category
    
    async def initialize(self) -> bool:
        """Initialize the CLIP model.
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            # Import here to avoid loading on module import
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            logger.info(f"Loading CLIP model: {self.model_name}")
            
            # Load in thread to not block
            loop = asyncio.get_event_loop()
            
            def load_model():
                model = CLIPModel.from_pretrained(self.model_name)
                processor = CLIPProcessor.from_pretrained(self.model_name)
                if self.device == "cuda" and torch.cuda.is_available():
                    model = model.to("cuda")
                return model, processor
            
            self._model, self._processor = await loop.run_in_executor(
                self._executor, load_model
            )
            
            self._initialized = True
            logger.info("CLIP model loaded successfully")
            return True
            
        except ImportError as e:
            logger.warning(
                f"ML dependencies not installed. Install with: "
                f"pip install transformers torch pillow. Error: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to initialize AutoTagger: {e}")
            return False
    
    async def analyze_image(
        self,
        image_path: Path,
        top_k: int = 10,
        threshold: float = 0.1
    ) -> AutoTagResult:
        """Analyze an image and generate tags.
        
        Args:
            image_path: Path to image file
            top_k: Number of top tags to return
            threshold: Minimum confidence threshold
            
        Returns:
            AutoTagResult with predicted tags
        """
        import time
        start_time = time.time()
        
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized:
            return AutoTagResult(
                file_path=str(image_path),
                tags=[],
                processing_time=time.time() - start_time
            )
        
        try:
            from PIL import Image
            import torch
            
            # Load and process image
            loop = asyncio.get_event_loop()
            
            def process_image():
                image = Image.open(image_path).convert("RGB")
                
                # Prepare inputs for CLIP
                text_inputs = self._processor(
                    text=self._all_tags,
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                )
                
                image_inputs = self._processor(
                    images=image,
                    return_tensors="pt"
                )
                
                if self.device == "cuda":
                    text_inputs = {k: v.cuda() for k, v in text_inputs.items()}
                    image_inputs = {k: v.cuda() for k, v in image_inputs.items()}
                
                # Get embeddings
                with torch.no_grad():
                    image_features = self._model.get_image_features(
                        **image_inputs
                    )
                    text_features = self._model.get_text_features(
                        **text_inputs
                    )
                    
                    # Normalize
                    image_features = image_features / image_features.norm(
                        dim=-1, keepdim=True
                    )
                    text_features = text_features / text_features.norm(
                        dim=-1, keepdim=True
                    )
                    
                    # Calculate similarities
                    similarities = (image_features @ text_features.T).squeeze()
                    
                    # Convert to probabilities with softmax
                    probs = torch.softmax(similarities * 100, dim=0)
                
                return probs.cpu().numpy(), image_features.cpu().numpy().flatten()
            
            probs, embeddings = await loop.run_in_executor(
                self._executor, process_image
            )
            
            # Get top predictions
            tag_predictions = []
            sorted_indices = probs.argsort()[::-1]
            
            for idx in sorted_indices[:top_k]:
                tag_name = self._all_tags[idx]
                confidence = float(probs[idx])
                
                if confidence >= threshold:
                    tag_predictions.append(
                        TagPrediction(
                            name=tag_name,
                            confidence=confidence,
                            category=self._tag_categories.get(tag_name, "general")
                        )
                    )
            
            processing_time = time.time() - start_time
            
            return AutoTagResult(
                file_path=str(image_path),
                tags=tag_predictions,
                embeddings=embeddings.tolist(),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze image {image_path}: {e}")
            return AutoTagResult(
                file_path=str(image_path),
                tags=[],
                processing_time=time.time() - start_time
            )
    
    async def analyze_video_keyframe(
        self,
        video_path: Path,
        timestamp: float = 5.0,
        top_k: int = 10,
        threshold: float = 0.1
    ) -> AutoTagResult:
        """Analyze a video by extracting and tagging a keyframe.
        
        Args:
            video_path: Path to video file
            timestamp: Timestamp in seconds to extract frame
            top_k: Number of top tags
            threshold: Minimum confidence
            
        Returns:
            AutoTagResult with predicted tags
        """
        import tempfile
        import subprocess
        
        try:
            # Extract frame using ffmpeg
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(tmp_path)
            ]
            
            subprocess.run(cmd, capture_output=True, timeout=30)
            
            if tmp_path.exists():
                result = await self.analyze_image(tmp_path, top_k, threshold)
                result.file_path = str(video_path)
                tmp_path.unlink()
                return result
            else:
                return AutoTagResult(file_path=str(video_path), tags=[])
                
        except Exception as e:
            logger.error(f"Failed to analyze video {video_path}: {e}")
            return AutoTagResult(file_path=str(video_path), tags=[])
    
    async def batch_analyze(
        self,
        paths: List[Path],
        top_k: int = 10,
        threshold: float = 0.1
    ) -> List[AutoTagResult]:
        """Analyze multiple files.
        
        Args:
            paths: List of file paths
            top_k: Number of top tags per file
            threshold: Minimum confidence
            
        Returns:
            List of AutoTagResults
        """
        results = []
        
        for path in paths:
            suffix = path.suffix.lower()
            
            if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
                result = await self.analyze_image(path, top_k, threshold)
            elif suffix in {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm"}:
                result = await self.analyze_video_keyframe(path, top_k=top_k, threshold=threshold)
            else:
                result = AutoTagResult(file_path=str(path), tags=[])
            
            results.append(result)
        
        return results
    
    def shutdown(self) -> None:
        """Clean up resources."""
        self._executor.shutdown(wait=False)
        self._model = None
        self._processor = None
        self._initialized = False


# Singleton instance
_auto_tagger: Optional[AutoTagger] = None


def get_auto_tagger() -> AutoTagger:
    """Get the global AutoTagger instance.
    
    Returns:
        AutoTagger singleton
    """
    global _auto_tagger
    if _auto_tagger is None:
        _auto_tagger = AutoTagger()
    return _auto_tagger


async def auto_tag_file(
    file_path: Path,
    top_k: int = 10,
    threshold: float = 0.3
) -> List[str]:
    """Convenience function to auto-tag a single file.
    
    Args:
        file_path: Path to media file
        top_k: Number of tags
        threshold: Confidence threshold
        
    Returns:
        List of tag names
    """
    tagger = get_auto_tagger()
    await tagger.initialize()
    
    suffix = file_path.suffix.lower()
    
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
        result = await tagger.analyze_image(file_path, top_k, threshold)
    elif suffix in {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm"}:
        result = await tagger.analyze_video_keyframe(file_path, top_k=top_k, threshold=threshold)
    else:
        return []
    
    return result.to_tag_names(threshold)
