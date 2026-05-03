"""Embedding generation: convert text chunks into dense vectors.

Supports two providers:
- ``local``  — sentence-transformers (no API key required, fully offline).
- ``openai`` — OpenAI ``text-embedding-3-small`` (requires ``OPENAI_API_KEY``).

The provider is selected via the ``EMBEDDING_PROVIDER`` environment variable.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.chunker import Chunk

logger = logging.getLogger(__name__)

_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local").lower()
_LOCAL_MODEL_NAME = "all-MiniLM-L6-v2"
_OPENAI_MODEL_NAME = "text-embedding-3-small"

# Module-level model cache (loaded lazily)
_local_model = None
_openai_client = None


def _get_local_model():
    global _local_model  # noqa: PLW0603
    if _local_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        logger.info("Loading local embedding model '%s'…", _LOCAL_MODEL_NAME)
        _local_model = SentenceTransformer(_LOCAL_MODEL_NAME)
    return _local_model


def _get_openai_client():
    global _openai_client  # noqa: PLW0603
    if _openai_client is None:
        from openai import OpenAI  # noqa: PLC0415

        _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return a float32 matrix of shape (N, D) for *texts*.

    Args:
        texts: List of strings to embed.

    Returns:
        NumPy array of shape ``(len(texts), embedding_dim)``.
    """
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    if _PROVIDER == "local":
        model = _get_local_model()
        vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return vectors.astype(np.float32)

    if _PROVIDER == "openai":
        client = _get_openai_client()
        response = client.embeddings.create(input=texts, model=_OPENAI_MODEL_NAME)
        vectors = [item.embedding for item in response.data]
        return np.array(vectors, dtype=np.float32)

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER '{_PROVIDER}'. Choose 'local' or 'openai'."
    )


def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    """Embed the text of each chunk and return the matrix of vectors."""
    texts = [c.text for c in chunks]
    return embed_texts(texts)


def embed_query(question: str) -> np.ndarray:
    """Embed a single query string and return a 1-D float32 vector."""
    matrix = embed_texts([question])
    return matrix[0]
