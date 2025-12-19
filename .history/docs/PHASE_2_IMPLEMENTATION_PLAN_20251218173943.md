# Phase 2: AI-Native Auto-Tagging & Semantic Search Implementation Plan

## Overview
Phase 2 builds on completed Phase 1 (Watch Folders + FTS5 Search) with intelligent, memory-augmented features using locally-deployable AI models.

**Target Timeline:** 2-3 weeks for MVP, 4-6 weeks for production-ready

---

## Architecture Decision: Tier-1 LLMs with Ollama

### Why This Approach

| Aspect | Benefit |
|--------|---------|
| **Cost** | Zero runtime costs (local inference) |
| **Privacy** | 100% data stays on user's machine |
| **Speed** | No network latency (Ollama on Windows 11) |
| **Control** | Full model customization, no API limits |
| **Scalability** | Linear cost with media volume |

### Model Stack Selection (Latest 2024 Models)

#### 1. **Embeddings Model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Size**: 22MB (runs on CPU or GPU)
- **Performance**: 383M+ downloads, MTEB top performer for efficiency
- **Use**: Generate semantic embeddings for media metadata
- **Latency**: ~10-50ms per embedding (GPU), ~100-200ms (CPU)
- **Dimensions**: 384 dimensions per embedding

#### 2. **Vision Model**: `Phi-4-multimodal-instruct`
- **Size**: 6B parameters
- **Modality**: Image + text understanding
- **Use**: Analyze visual content + text overlay in images
- **Ollama Support**: Yes (via GGUF quantization)
- **Latency**: ~500ms-2s per image (GPU), ~5-10s (CPU)

#### 3. **General LLM**: `Phi-4-mini-instruct` or `Mistral-7B`
- **Phi-4-mini**: 4B parameters, faster
- **Mistral-7B**: 7B parameters, higher quality
- **Use**: Context-aware tagging, description generation
- **Ollama Support**: Yes (pre-quantized available)
- **Latency**: ~100-500ms (GPU), ~2-5s (CPU)

#### 4. **Clustering/Semantic Search**: `umap-learn` + `hdbscan`
- **Purpose**: Group similar media semantically
- **Advantage**: Fast, no model needed, pure algorithm
- **Integration**: Python libraries (already available)

---

## Implementation Phases

### Phase 2A: Core Infrastructure (Week 1)

#### Step 1: Ollama Integration Setup
```bash
# Windows 11 setup
1. Download Ollama: https://ollama.ai/download/windows
2. Install to default location (C:\Users\{user}\AppData\Local\Programs\Ollama)
3. Verify Ollama API: http://localhost:11434/api/tags

# Pull initial models (one-time, ~15-20 min on fast connection)
ollama pull all-minilm-l6-v2        # 24MB
ollama pull phi4:4b                 # 2.4GB (or phi-4-mini when available)
ollama pull mistral:7b              # 4GB (optional, alternative LLM)
```

#### Step 2: Python Integration Layer
**File**: `src/core/ai_engine.py` (NEW)
```python
from ollama import Client
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Tuple

class AIEngine:
    """Local AI inference using Ollama + SentenceTransformers"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama = Client(host=ollama_host)
        self.embeddings = SentenceTransformer(
            'sentence-transformers/all-MiniLM-L6-v2',
            cache_folder='.cache'
        )
        self.embedding_dim = 384
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate semantic embeddings (fast, CPU-friendly)"""
        return self.embeddings.encode(texts, convert_to_numpy=True)
    
    def generate_tags(self, description: str, image_context: str = None) -> List[str]:
        """Generate tags using Phi-4-mini (context-aware)"""
        prompt = f"""Analyze this media and suggest 5-10 tags.
        Description: {description}
        Visual: {image_context or 'Not provided'}
        
        Return ONLY a JSON list of tags, nothing else:
        ["tag1", "tag2", ...]"""
        
        response = self.ollama.generate(
            model="phi4:4b",
            prompt=prompt,
            stream=False,
            options={"temperature": 0.3}
        )
        return parse_json_tags(response['response'])
    
    def analyze_image(self, image_path: str) -> str:
        """Analyze image content using Phi-4-multimodal"""
        # Load image as base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        response = self.ollama.generate(
            model="phi4:multimodal",
            prompt="Describe this image in 1-2 sentences for tagging purposes.",
            images=[image_data],
            stream=False,
            options={"temperature": 0.3}
        )
        return response['response'].strip()
```

#### Step 3: Database Schema Additions
**File**: `alembic/versions/0002_add_ai_features.py` (NEW)
```python
# Add to media table:
# - semantic_embedding: BLOB (384 * 4 bytes for float32)
# - embedding_version: TEXT (track model version)
# - ai_tags: JSON (auto-generated tags with confidence)
# - visual_description: TEXT (from multimodal analysis)
# - embedding_processed_at: TIMESTAMP

# Create semantic search index
# - CREATE INDEX idx_media_embeddings USING VECTOR (semantic_embedding)
```

---

### Phase 2B: Auto-Tagging System (Week 1-2)

#### Step 4: Tag Generation Pipeline
**File**: `src/core/tagger.py` (NEW)
```python
class AutoTagger:
    """Generate and cache semantic tags for media"""
    
    def __init__(self, ai_engine: AIEngine, db: Database):
        self.ai = ai_engine
        self.db = db
        
    async def process_media_batch(self, media_ids: List[int], 
                                  use_visual: bool = True):
        """Batch process media for tagging"""
        for media_id in media_ids:
            media = self.db.get_media(media_id)
            
            # 1. Get visual analysis if image
            visual_context = ""
            if use_visual and media.is_image:
                visual_context = self.ai.analyze_image(media.file_path)
            
            # 2. Generate embeddings from metadata
            metadata_text = f"{media.title} {media.description}"
            embedding = self.ai.generate_embeddings([metadata_text])[0]
            
            # 3. Generate tags
            tags = self.ai.generate_tags(metadata_text, visual_context)
            
            # 4. Store in database
            self.db.update_media(media_id, {
                'semantic_embedding': embedding.tobytes(),
                'ai_tags': json.dumps(tags),
                'visual_description': visual_context,
                'embedding_processed_at': datetime.now()
            })
```

#### Step 5: Incremental Tagging on Watch
**File**: `src/core/scanner.py` (MODIFY)
```python
# Add to scanner when new media detected:
auto_tagger = AutoTagger(ai_engine, db)
await auto_tagger.process_media_batch([new_media.id])
```

---

### Phase 2C: Semantic Search & Clustering (Week 2)

#### Step 6: Vector Database Integration
**File**: `src/core/semantic_search.py` (NEW)
```python
import umap
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity

class SemanticSearchEngine:
    """Semantic search + automatic collection clustering"""
    
    def __init__(self, ai_engine: AIEngine, db: Database):
        self.ai = ai_engine
        self.db = db
        self.umap_reducer = umap.UMAP(n_components=16)  # Compress 384→16 dims
        self.clusterer = hdbscan.HDBSCAN(min_cluster_size=3)
        
    def search_semantic(self, query: str, top_k: int = 20) -> List[Media]:
        """Find similar media using semantic search"""
        # 1. Embed query
        query_embedding = self.ai.generate_embeddings([query])[0]
        
        # 2. Get all embeddings from database
        all_embeddings = self.db.get_all_embeddings()
        
        # 3. Compute similarity
        similarities = cosine_similarity(
            [query_embedding], 
            all_embeddings
        )[0]
        
        # 4. Return top-k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.db.get_media_by_index(idx) for idx in top_indices]
    
    def auto_cluster_media(self) -> Dict[str, List[Media]]:
        """Automatically discover semantic collections"""
        # 1. Get all embeddings
        embeddings = self.db.get_all_embeddings()
        
        # 2. Reduce dimensions (for speed)
        reduced = self.umap_reducer.fit_transform(embeddings)
        
        # 3. Cluster
        labels = self.clusterer.fit_predict(reduced)
        
        # 4. Create collections
        clusters = {}
        for label, media_id in enumerate(self.db.get_all_media_ids()):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(self.db.get_media(media_id))
        
        return clusters
```

#### Step 7: Database Optimization
**File**: `src/core/database.py` (MODIFY)
```python
# Add methods:
def get_all_embeddings() -> np.ndarray:
    """Fast fetch of all embeddings for clustering"""
    
def get_media_by_index(idx: int) -> Media:
    """Quick lookup by embedding index"""
    
def bulk_update_embeddings(updates: Dict[int, bytes]):
    """Batch update embeddings"""
```

---

### Phase 2D: API & CLI Integration (Week 2-3)

#### Step 8: REST API Endpoints
**File**: `src/api/routers/search.py` (NEW)
```python
from fastapi import APIRouter, Query
from src.core.semantic_search import SemanticSearchEngine

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("/semantic")
async def semantic_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(20, ge=1, le=100)
):
    """Search media by semantic similarity"""
    results = search_engine.search_semantic(query, top_k)
    return {"results": [m.to_dict() for m in results]}

@router.get("/tags")
async def get_ai_tags(media_id: int):
    """Get AI-generated tags for media"""
    media = db.get_media(media_id)
    return {"tags": media.ai_tags, "confidence": 0.85}

@router.post("/regenerate-tags")
async def regenerate_tags(media_id: int):
    """Re-generate tags for a specific media"""
    await auto_tagger.process_media_batch([media_id])
    return {"status": "processing"}

@router.get("/collections")
async def get_auto_collections():
    """Get AI-discovered semantic collections"""
    collections = search_engine.auto_cluster_media()
    return {"collections": format_collections(collections)}
```

#### Step 9: CLI Commands
**File**: `src/cli/commands/ai.py` (NEW)
```python
import click
from src.core.tagger import AutoTagger
from src.core.semantic_search import SemanticSearchEngine

@click.group()
def ai():
    """AI-powered tagging and search"""
    pass

@ai.command()
@click.option('--media-id', type=int, help='Process single media')
@click.option('--use-visual/--no-visual', default=True)
def tag(media_id, use_visual):
    """Generate tags for media"""
    if media_id:
        auto_tagger.process_media_batch([media_id], use_visual=use_visual)
    else:
        all_media = db.get_all_media()
        auto_tagger.process_media_batch([m.id for m in all_media], use_visual=use_visual)

@ai.command()
@click.argument('query')
@click.option('--top-k', default=20, type=int)
def search(query, top_k):
    """Search media semantically"""
    results = search_engine.search_semantic(query, top_k)
    for media in results:
        click.echo(f"{media.title} ({media.ai_tags})")

@ai.command()
def cluster():
    """Auto-discover semantic collections"""
    collections = search_engine.auto_cluster_media()
    click.echo(f"Found {len(collections)} collections")
    for label, media_list in collections.items():
        click.echo(f"  Collection {label}: {len(media_list)} items")
```

---

## Deployment Strategy

### Development (Windows 11)
```bash
# 1. Start Ollama (system tray icon handles this)
ollama serve  # or just open Ollama app

# 2. Start MediaForge with AI
python -m src.cli.main --with-ai

# 3. Test semantic search
mediaforge search "sunset landscape"
mediaforge ai tag --use-visual
```

### Performance Characteristics

| Operation | GPU (RTX 3060) | CPU (Ryzen 5600) |
|-----------|----------------|------------------|
| Embedding 100 texts | ~0.5s | ~2-3s |
| Image analysis | ~0.5s | ~5-10s |
| Generate tags | ~0.3s | ~1-2s |
| Semantic search (1000 items) | ~0.1s | ~0.5s |
| Auto-cluster (1000 items) | ~2s | ~10s |

### Resource Requirements

| Component | Disk | RAM | GPU Memory |
|-----------|------|-----|-----------|
| Ollama (Phi-4-mini + Mistral) | 6-7GB | 4GB (for 4B model) | 4GB (optional) |
| Embeddings cache | ~100MB/10k items | 1GB | - |
| Total | 7-8GB | 6GB | 4-6GB |

---

## Key Features

### ✅ Complete in Phase 2

1. **Incremental Auto-Tagging**
   - Background tag generation for new media
   - Manual re-tagging available via CLI/API
   - Confidence scoring

2. **Semantic Search**
   - Query-by-description
   - Similar media discovery
   - Fast (vector similarity)

3. **Auto-Collections**
   - HDBSCAN clustering
   - Semantic grouping
   - Collection management API

4. **Visual Analysis** (Images)
   - Multimodal understanding
   - OCR-friendly (text detection)
   - Integration with manual tagging

5. **Offline-First**
   - Zero cloud dependency
   - Full privacy
   - Works without internet

### 🔮 Future Enhancements (Phase 3+)

- Custom model fine-tuning
- Video understanding (frames → tags)
- Audio analysis + transcription
- Cross-modal search (search by image)
- Advanced clustering (hierarchical)
- User feedback loop learning

---

## Testing Strategy

### Unit Tests
```python
# test_ai_engine.py
- Embedding generation
- Tag parsing
- Model availability checks

# test_semantic_search.py
- Query processing
- Similarity ranking
- Clustering stability
```

### Integration Tests
```python
# test_tagger_integration.py
- End-to-end tagging pipeline
- Database persistence
- Batch processing

# test_api_search.py
- REST endpoint correctness
- Response formatting
```

### Performance Tests
```python
# test_ai_performance.py
- Embedding speed benchmarks
- Memory usage under load
- Batch processing efficiency
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Ollama not available | Graceful degradation, fallback to keyword search |
| OOM on large batches | Implement pagination, streaming |
| Slow initial processing | Background processing, progress indicators |
| Model hallucinations | Confidence thresholds, manual review option |

---

## Success Metrics

- ✅ Semantic search latency < 100ms (CPU)
- ✅ Auto-tagging accuracy > 80% (manual verification)
- ✅ Memory usage < 8GB total
- ✅ 100% offline operation
- ✅ Zero API dependencies

---

## Next Steps

1. **Immediate (Today)**
   - Install Ollama on Windows 11
   - Pull recommended models
   - Create `src/core/ai_engine.py`

2. **This Week**
   - Implement embedding generation
   - Add database schema for embeddings
   - Create auto-tagger service

3. **Next Week**
   - Implement semantic search
   - Add UMAP + HDBSCAN clustering
   - Create REST API endpoints

4. **Week 3**
   - CLI integration
   - End-to-end testing
   - Performance optimization

---

## References

- [Ollama Documentation](https://ollama.ai/library)
- [Sentence Transformers MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard)
- [Phi-4 Model Card](https://huggingface.co/microsoft/phi-4)
- [HDBSCAN Documentation](https://hdbscan.readthedocs.io/)
