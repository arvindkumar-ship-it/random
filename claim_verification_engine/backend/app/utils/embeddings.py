from app.config import settings
import numpy as np

_model = None


def get_client():
    """Loads local sentence-transformers model once (no API, no cost)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def get_embedding(text: str, model: str = None) -> np.ndarray:
    """Get embedding vector for text using a local model"""
    st_model = get_client()
    return np.array(st_model.encode(text))


def get_embeddings_batch(texts: list) -> np.ndarray:
    """Encode many texts in one batched call — much faster than one-by-one."""
    st_model = get_client()
    return np.array(st_model.encode(texts))
