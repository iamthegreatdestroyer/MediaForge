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
