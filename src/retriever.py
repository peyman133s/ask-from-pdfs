"""Retriever: orchestrate query embedding and vector store search."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from src import embedder, vector_store

logger = logging.getLogger(__name__)

_INDEX_DIR = os.getenv("INDEX_DIR", "data/index")
_TOP_K = int(os.getenv("TOP_K", "3"))


def retrieve(question: str, top_k: int | None = None, index_dir: str | Path | None = None) -> list[dict]:
    """Embed *question*, search the local index, and return the top matching chunks.

    Args:
        question:  The user's natural-language question.
        top_k:     Number of chunks to return (defaults to ``TOP_K`` env var).
        index_dir: Path to the persisted index (defaults to ``INDEX_DIR`` env var).

    Returns:
        A list of chunk dicts with keys ``filename``, ``chunk_index``, and ``text``.
    """
    if top_k is None:
        top_k = _TOP_K
    if index_dir is None:
        index_dir = _INDEX_DIR

    logger.debug("Embedding query: %r", question)
    query_vector = embedder.embed_query(question)

    index, chunks = vector_store.load(index_dir)
    results = vector_store.search(index, chunks, query_vector, top_k=top_k)
    logger.debug("Retrieved %d chunk(s)", len(results))
    return results
