"""
AI Engine for local inference using Ollama + SentenceTransformers
Handles embeddings, tag generation, and image analysis
"""

import asyncio
import json
import base64
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

try:
    from ollama import Client
except ImportError:
    Client = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class AIEngine:
    """Local AI inference engine using Ollama and SentenceTransformers"""
    
    # Model configurations
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    TAG_MODEL = "phi4:4b"
    MULTIMODAL_MODEL = "phi4:multimodal"
    
    def __init__(self, ollama_host: str = "http://localhost:11434", 
                 embeddings_cache_dir: str = ".cache/embeddings"):
        """
        Initialize AI Engine
        
        Args:
            ollama_host: Ollama API endpoint
            embeddings_cache_dir: Directory for embedding cache
        """
        self.ollama_host = ollama_host
        self.cache_dir = Path(embeddings_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.ollama = None
        self.embeddings_model = None
        self._init_components()
        
    def _init_components(self):
        """Initialize Ollama and Embeddings model"""
        # Try Ollama connection
        if Client:
            try:
                self.ollama = Client(host=self.ollama_host)
                # Test connection
                tags = self.ollama.list()
                logger.info(f"✅ Ollama connected. Available models: {[t.name for t in tags.models]}")
            except Exception as e:
                logger.warning(f"⚠️  Ollama not available: {e}")
                self.ollama = None
        
        # Load embeddings model
        if SentenceTransformer:
            try:
                logger.info("Loading embeddings model...")
                self.embeddings_model = SentenceTransformer(
                    self.EMBEDDING_MODEL,
                    cache_folder=str(self.cache_dir)
                )
                logger.info(f"✅ Embeddings model loaded (dim={self.embeddings_model.get_sentence_embedding_dimension()})")
            except Exception as e:
                logger.error(f"❌ Failed to load embeddings model: {e}")
                self.embeddings_model = None
    
    def is_available(self) -> bool:
        """Check if AI engine is ready to use"""
        return self.embeddings_model is not None or self.ollama is not None
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate semantic embeddings for text
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Embeddings as numpy array (n_texts, 384)
        """
        if not self.embeddings_model:
            logger.warning("Embeddings model not loaded")
            return np.zeros((len(texts), 384))
        
        try:
            embeddings = self.embeddings_model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return np.zeros((len(texts), 384))
    
    async def generate_tags_async(self, 
                                  description: str, 
                                  image_context: str = None,
                                  max_tags: int = 10,
                                  temperature: float = 0.3) -> List[str]:
        """
        Generate tags using LLM (async wrapper)
        
        Args:
            description: Media metadata/description
            image_context: Visual analysis results
            max_tags: Maximum number of tags
            temperature: Model temperature (0=deterministic)
            
        Returns:
            List of generated tags
        """
        if not self.ollama:
            logger.warning("Ollama not available, returning empty tags")
            return []
        
        return await asyncio.to_thread(
            self.generate_tags,
            description,
            image_context,
            max_tags,
            temperature
        )
    
    def generate_tags(self, 
                     description: str, 
                     image_context: str = None,
                     max_tags: int = 10,
                     temperature: float = 0.3) -> List[str]:
        """
        Generate tags using LLM (synchronous)
        
        Args:
            description: Media metadata/description
            image_context: Visual analysis results
            max_tags: Maximum number of tags
            temperature: Model temperature
            
        Returns:
            List of generated tags
        """
        if not self.ollama:
            return []
        
        try:
            prompt = f"""You are a media tagging AI. Analyze this media and suggest {max_tags} relevant tags.

Description: {description}
{f'Visual Analysis: {image_context}' if image_context else ''}

Return ONLY a JSON list of tags (strings only), no other text:
["tag1", "tag2", "tag3"]"""

            response = self.ollama.generate(
                model=self.TAG_MODEL,
                prompt=prompt,
                stream=False,
                options={
                    "temperature": temperature,
                    "top_k": 40,
                    "top_p": 0.9
                }
            )
            
            # Parse JSON response
            response_text = response['response'].strip()
            
            # Try to extract JSON
            if '[' in response_text and ']' in response_text:
                json_str = response_text[response_text.index('['):response_text.rindex(']')+1]
                tags = json.loads(json_str)
                return [str(t).strip() for t in tags if t][:max_tags]
            
            return []
            
        except Exception as e:
            logger.error(f"Tag generation failed: {e}")
            return []
    
    async def analyze_image_async(self, image_path: str) -> str:
        """Async wrapper for image analysis"""
        return await asyncio.to_thread(self.analyze_image, image_path)
    
    def analyze_image(self, image_path: str) -> str:
        """
        Analyze image content using multimodal model
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image description for tagging
        """
        if not self.ollama or not Path(image_path).exists():
            return ""
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            response = self.ollama.generate(
                model=self.MULTIMODAL_MODEL,
                prompt="Analyze this image and describe it in 1-2 sentences for media tagging purposes. Focus on: objects, scenes, colors, style, mood.",
                images=[image_data],
                stream=False,
                options={"temperature": 0.2}
            )
            
            return response['response'].strip()
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return ""
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Get list of available Ollama models"""
        if not self.ollama:
            return {"status": "offline"}
        
        try:
            tags = self.ollama.list()
            return {
                "embedding": [self.EMBEDDING_MODEL],
                "tagging": [self.TAG_MODEL],
                "multimodal": [self.MULTIMODAL_MODEL],
                "available": [t.name for t in tags.models]
            }
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return {}
    
    def embedding_to_bytes(self, embedding: np.ndarray) -> bytes:
        """Convert embedding to bytes for storage"""
        return embedding.astype(np.float32).tobytes()
    
    @staticmethod
    def bytes_to_embedding(data: bytes) -> np.ndarray:
        """Convert stored bytes back to embedding"""
        return np.frombuffer(data, dtype=np.float32)


# Singleton instance
_ai_engine: Optional[AIEngine] = None


def get_ai_engine() -> AIEngine:
    """Get or create AI Engine singleton"""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine


def is_ai_available() -> bool:
    """Check if AI features are available"""
    engine = get_ai_engine()
    return engine.is_available()
