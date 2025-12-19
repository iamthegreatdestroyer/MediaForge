"""Quick test of AI Engine setup"""
from src.core.ai_engine import get_ai_engine
from src.core.semantic_search import get_search_engine
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

print("\n" + "="*60)
print("🚀 PHASE 2 AI ENGINE TEST")
print("="*60 + "\n")

print("[1/3] Testing AI Engine initialization...")
engine = get_ai_engine()
print(f"      AI Engine available: {engine.is_available()}")

if engine.embeddings_model:
    print("      ✅ Embeddings model loaded")
    
    # Test embeddings
    texts = ["sunset landscape", "nature documentary"]
    embeddings = engine.generate_embeddings(texts)
    print(f"      ✅ Generated embeddings shape: {embeddings.shape}")
else:
    print("      ⚠️  Embeddings model not available")

print("\n[2/3] Testing Ollama connection...")
if engine.ollama:
    print("      ✅ Ollama connection active")
    models = engine.get_available_models()
    available = models.get("available", [])
    if available:
        print(f"      ✅ Available models: {len(available)}")
        for model in available[:3]:
            print(f"         - {model}")
else:
    print("      ⚠️  Ollama not connected (will use local models only)")

print("\n[3/3] Testing Semantic Search Engine...")
search_engine = get_search_engine()
print("      ✅ Semantic Search Engine initialized")
print(f"      - UMAP available: {search_engine.umap_reducer is not None}")
print(f"      - HDBSCAN available: {search_engine.clusterer is not None}")

print("\n" + "="*60)
print("🎉 PHASE 2 FOUNDATION READY!")
print("="*60)
print("\nNext Steps:")
print("  1. Database schema updates (add embedding columns)")
print("  2. Auto-tagging service implementation")
print("  3. REST API endpoints")
print("  4. CLI commands")
print("\n")
