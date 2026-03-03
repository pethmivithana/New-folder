"""
tfidf_registry.py
─────────────────
Shared singleton registry for the standalone tfidf_vectorizer.pkl.
This vectorizer is used by:
  - ai_routes.py  (story point prediction)
  - sprint_goal_alignment.py  (semantic similarity)

Separate from the TF-IDF inside effort_artifacts.pkl which is owned
by feature_engineering.py for effort model feature building.
"""

from __future__ import annotations
import warnings
import numpy as np
from typing import Optional

_standalone_tfidf = None


def set_standalone_tfidf(vec) -> None:
    global _standalone_tfidf
    _standalone_tfidf = vec


def get_standalone_tfidf():
    return _standalone_tfidf


def tfidf_transform(texts: list[str]) -> Optional[np.ndarray]:
    """
    Transform a list of texts using the standalone TF-IDF vectorizer.
    Returns a dense numpy array of shape (n_texts, n_features), or None if
    the vectorizer is not loaded.
    """
    global _standalone_tfidf
    if _standalone_tfidf is None:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            result = _standalone_tfidf.transform(texts)
            if hasattr(result, 'toarray'):
                return result.toarray()
            return np.array(result)
    except Exception as e:
        import sys
        print(f"[TFIDF_REGISTRY] Transform error: {e}", file=sys.stderr)
        return None


def tfidf_cosine_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using the standalone TF-IDF vectorizer.
    Returns a float in [0, 1]. Returns -1.0 if vectorizer is not available.
    """
    global _standalone_tfidf
    if _standalone_tfidf is None:
        return -1.0
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            vecs = _standalone_tfidf.transform([text_a, text_b])
            if hasattr(vecs, 'toarray'):
                vecs = vecs.toarray()
            a, b = vecs[0], vecs[1]
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return float(np.dot(a, b) / (norm_a * norm_b))
    except Exception as e:
        import sys
        print(f"[TFIDF_REGISTRY] Cosine similarity error: {e}", file=sys.stderr)
        return -1.0


def tfidf_feature_vector(text: str) -> Optional[np.ndarray]:
    """
    Get the TF-IDF feature vector for a single text string.
    Returns 1D numpy array or None.
    """
    result = tfidf_transform([text])
    if result is None:
        return None
    return result[0]


def is_tfidf_available() -> bool:
    return _standalone_tfidf is not None