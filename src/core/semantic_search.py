"""
Semantic Search Engine using embeddings and clustering
"""

import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.preprocessing import StandardScaler
except ImportError:
    cosine_similarity = None
    StandardScaler = None

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False

from src.models.media import MediaItem
from src.core.ai_engine import get_ai_engine

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with metadata"""
    media: MediaItem
    similarity_score: float
    rank: int


class SemanticSearchEngine:
    """
    Semantic search and clustering engine
    
    Features:
    - Query-by-embedding semantic search
    - UMAP dimensionality reduction
    - HDBSCAN clustering for auto-collections
    - Similarity ranking and re-ranking
    """
    
    def __init__(self, embedding_dim: int = 384):
        """
        Initialize semantic search engine
        
        Args:
            embedding_dim: Embedding dimension (typically 384 for MiniLM)
        """
        self.embedding_dim = embedding_dim
        self.ai_engine = get_ai_engine()
        
        # Initialize optional components
        self.umap_reducer = None
        self.clusterer = None
        self._init_optional_components()
        
        logger.info("✅ SemanticSearchEngine initialized")
    
    def _init_optional_components(self):
        """Initialize optional ML components"""
        if UMAP_AVAILABLE:
            try:
                self.umap_reducer = umap.UMAP(
                    n_components=16,
                    metric='cosine',
                    n_neighbors=15,
                    min_dist=0.1,
                    verbose=False
                )
                logger.info("✅ UMAP dimensionality reduction available")
            except Exception as e:
                logger.warning(f"⚠️  UMAP not available: {e}")
        
        if HDBSCAN_AVAILABLE:
            try:
                self.clusterer = hdbscan.HDBSCAN(
                    min_cluster_size=3,
                    min_samples=1,
                    metric='cosine',
                    allow_single_cluster=False
                )
                logger.info("✅ HDBSCAN clustering available")
            except Exception as e:
                logger.warning(f"⚠️  HDBSCAN not available: {e}")
    
    def search_semantic(self, 
                       query: str,
                       all_embeddings: np.ndarray,
                       media_list: List[MediaItem],
                       top_k: int = 20,
                       similarity_threshold: float = 0.0) -> List[SearchResult]:
        """
        Search media by semantic similarity to query
        
        Args:
            query: Search query string
            all_embeddings: All media embeddings (n, 384)
            media_list: Corresponding MediaItem objects
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects, ranked by similarity
        """
        if not cosine_similarity:
            logger.warning("cosine_similarity not available")
            return []
        
        if len(all_embeddings) == 0:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.ai_engine.generate_embeddings([query])[0]
            
            # Compute similarities
            similarities = cosine_similarity(
                [query_embedding],
                all_embeddings
            )[0]
            
            # Filter by threshold and sort
            valid_indices = np.where(similarities >= similarity_threshold)[0]
            sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
            
            # Build results
            results = [
                SearchResult(
                    media=media_list[idx],
                    similarity_score=float(similarities[idx]),
                    rank=rank
                )
                for rank, idx in enumerate(sorted_indices[:top_k])
            ]
            
            logger.info(f"Found {len(results)} results for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def cluster_embeddings(self, 
                          embeddings: np.ndarray,
                          media_list: List[MediaItem]) -> Dict[int, List[MediaItem]]:
        """
        Cluster embeddings into semantic groups
        
        Args:
            embeddings: All media embeddings (n, 384)
            media_list: Corresponding MediaItem objects
            
        Returns:
            Dictionary mapping cluster ID to list of MediaItems
        """
        if not HDBSCAN_AVAILABLE or not self.clusterer:
            logger.warning("Clustering not available")
            return {-1: media_list}  # All in one "cluster"
        
        if len(embeddings) < 3:
            return {0: media_list}  # Too few items to cluster
        
        try:
            # Reduce dimensions if possible
            if self.umap_reducer and len(embeddings) > 10:
                reduced = self.umap_reducer.fit_transform(embeddings)
                logger.info(f"Reduced embeddings: {embeddings.shape} → {reduced.shape}")
            else:
                reduced = embeddings
            
            # Cluster
            labels = self.clusterer.fit_predict(reduced)
            
            # Group by cluster
            clusters: Dict[int, List[MediaItem]] = {}
            for label, media in zip(labels, media_list):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(media)
            
            logger.info(f"Created {len(clusters)} semantic clusters")
            return clusters
            
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return {-1: media_list}
    
    def rerank_by_tags(self,
                       results: List[SearchResult],
                       query_tags: List[str]) -> List[SearchResult]:
        """
        Re-rank search results by tag overlap with query
        
        Args:
            results: Initial search results
            query_tags: Tags extracted from query
            
        Returns:
            Re-ranked results
        """
        if not query_tags:
            return results
        
        query_tags_set = set(tag.lower() for tag in query_tags)
        
        # Score by tag overlap
        for result in results:
            media_tags_set = set(
                tag.lower() for tag in (result.media.tags or [])
            )
            overlap = len(query_tags_set & media_tags_set)
            tag_score = overlap / len(query_tags_set) if query_tags_set else 0
            
            # Boost similarity score by tag overlap
            result.similarity_score = 0.8 * result.similarity_score + 0.2 * tag_score
        
        # Re-sort by boosted score
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        for rank, result in enumerate(results):
            result.rank = rank
        
        return results
    
    def hybrid_search(self,
                     query: str,
                     all_embeddings: np.ndarray,
                     media_list: List[MediaItem],
                     fts_results: Optional[List[MediaItem]] = None,
                     top_k: int = 20) -> List[SearchResult]:
        """
        Hybrid search combining semantic + FTS5 results
        
        Args:
            query: Search query
            all_embeddings: All embeddings
            media_list: All media items
            fts_results: Optional FTS5 results to boost
            top_k: Number of results
            
        Returns:
            Hybrid search results
        """
        # Get semantic results
        semantic = self.search_semantic(
            query, all_embeddings, media_list, top_k*2
        )
        
        # Boost FTS5 results if provided
        if fts_results:
            fts_ids = {m.id for m in fts_results}
            for result in semantic:
                if result.media.id in fts_ids:
                    result.similarity_score *= 1.2  # Boost FTS5 matches
            
            semantic.sort(key=lambda r: r.similarity_score, reverse=True)
        
        return semantic[:top_k]
    def cluster_embeddings(
        self,
        embeddings: np.ndarray,
        media_items: List[MediaItem]
    ) -> Dict[int, List[MediaItem]]:
        """
        Automatically cluster similar media using embeddings
        
        Args:
            embeddings: Array of embeddings (n_items, embedding_dim)
            media_items: List of MediaItem objects
            
        Returns:
            Dictionary mapping cluster_id to list of media items
        """
        if not self.clusterer or len(embeddings) < 3:
            logger.warning("Clustering not available or insufficient data")
            return {}
        
        try:
            # Perform clustering
            self.clusterer.fit(embeddings)
            labels = self.clusterer.labels_
            
            # Group by cluster
            clusters = {}
            for media, label in zip(media_items, labels):
                # Ignore noise points (label == -1)
                if label >= 0:
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(media)
            
            logger.info(f"Created {len(clusters)} semantic clusters")
            return clusters
        
        except Exception as e:
            logger.error(f"Clustering error: {e}", exc_info=True)
            return {}

# Singleton instance
_search_engine: Optional[SemanticSearchEngine] = None


def get_search_engine() -> SemanticSearchEngine:
    """Get or create semantic search engine singleton"""
    global _search_engine
    if _search_engine is None:
        _search_engine = SemanticSearchEngine()
    return _search_engine
