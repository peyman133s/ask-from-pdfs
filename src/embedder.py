"""Embedding generation: convert text chunks into dense vectors locally."""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.chunker import Chunk

logger = logging.getLogger(__name__)

_DEFAULT_LOCAL_MODEL_PATH = "models/all-MiniLM-L6-v2"
_LOCAL_MODEL_NAME = os.getenv("LOCAL_EMBEDDING_MODEL", _DEFAULT_LOCAL_MODEL_PATH)

# Module-level model cache (loaded lazily)
_local_model = None


def _get_local_model():
    global _local_model  # noqa: PLW0603
    if _local_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        cache_folder = os.getenv("SENTENCE_TRANSFORMERS_HOME")
        offline_env = os.getenv("HF_HUB_OFFLINE", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        local_files_only = offline_env or os.path.isdir(_LOCAL_MODEL_NAME)

        logger.info("Loading local embedding model '%s'…", _LOCAL_MODEL_NAME)
        try:
            _local_model = SentenceTransformer(
                _LOCAL_MODEL_NAME,
                cache_folder=cache_folder,
                local_files_only=local_files_only,
            )
        except OSError as exc:
            if local_files_only:
                raise RuntimeError(
                    "Local embedding model is not available. Download it once with "
                    "`scripts/local download-embedding-model`, or set "
                    "LOCAL_EMBEDDING_MODEL to an existing sentence-transformers "
                    f"model directory. Current value: '{_LOCAL_MODEL_NAME}'."
                ) from exc
            raise
    return _local_model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return a float32 matrix of shape (N, D) for *texts*.

    Args:
        texts: List of strings to embed.

    Returns:
        NumPy array of shape ``(len(texts), embedding_dim)``.
    """
    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    model = _get_local_model()
    vectors = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return vectors.astype(np.float32)


def embed_chunks(chunks: list[Chunk]) -> np.ndarray:
    """Embed the text of each chunk and return the matrix of vectors."""
    texts = [c.text for c in chunks]
    return embed_texts(texts)


def embed_query(question: str) -> np.ndarray:
    """Embed a single query string and return a 1-D float32 vector."""
    matrix = embed_texts([question])
    return matrix[0]
