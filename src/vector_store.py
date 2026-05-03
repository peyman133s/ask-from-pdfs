"""Vector store: save and load a FAISS index together with chunk metadata."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import faiss
import numpy as np

if TYPE_CHECKING:
    from src.chunker import Chunk

logger = logging.getLogger(__name__)

_INDEX_FILE = "index.faiss"
_CHUNKS_FILE = "chunks.json"


def save(chunks: list[Chunk], vectors: np.ndarray, index_dir: str | Path) -> None:
    """Build a FAISS flat-L2 index from *vectors* and persist it to *index_dir*.

    Chunk metadata is saved alongside the index as a JSON file so it can be
    reloaded without re-running the whole ingestion pipeline.

    Args:
        chunks:    List of :class:`~src.chunker.Chunk` objects (same order as *vectors*).
        vectors:   Float32 matrix of shape ``(len(chunks), embedding_dim)``.
        index_dir: Directory where the index and metadata are written.
    """
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    vectors = np.array(vectors, dtype=np.float32)
    dim = vectors.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    faiss.write_index(index, str(index_dir / _INDEX_FILE))

    chunk_dicts = [asdict(c) for c in chunks]
    with open(index_dir / _CHUNKS_FILE, "w", encoding="utf-8") as fh:
        json.dump(chunk_dicts, fh, ensure_ascii=False, indent=2)

    logger.info("Saved index with %d vectors (dim=%d) to %s", index.ntotal, dim, index_dir)


def load(index_dir: str | Path) -> tuple[faiss.IndexFlatL2, list[dict]]:
    """Load the FAISS index and chunk metadata from *index_dir*.

    Returns:
        A tuple of ``(faiss_index, chunks_list)`` where each element of
        ``chunks_list`` is a plain dict with keys ``filename``, ``chunk_index``,
        and ``text``.

    Raises:
        FileNotFoundError: If the index files are missing.
    """
    index_dir = Path(index_dir)
    index_path = index_dir / _INDEX_FILE
    chunks_path = index_dir / _CHUNKS_FILE

    if not index_path.exists() or not chunks_path.exists():
        raise FileNotFoundError(
            f"Index not found in '{index_dir}'. Run 'python -m src.cli index' first."
        )

    index = faiss.read_index(str(index_path))
    with open(chunks_path, encoding="utf-8") as fh:
        chunks = json.load(fh)

    logger.info("Loaded index with %d vectors from %s", index.ntotal, index_dir)
    return index, chunks


def search(
    index: faiss.IndexFlatL2,
    chunks: list[dict],
    query_vector: np.ndarray,
    top_k: int = 3,
) -> list[dict]:
    """Return the *top_k* chunk dicts most similar to *query_vector*.

    Args:
        index:        A loaded FAISS index.
        chunks:       The list of chunk dicts loaded from disk (same order as the index).
        query_vector: 1-D float32 embedding of the query.
        top_k:        Number of results to return.

    Returns:
        List of chunk dicts (each with ``filename``, ``chunk_index``, ``text``).
    """
    query_vector = np.array(query_vector, dtype=np.float32).reshape(1, -1)
    k = min(top_k, index.ntotal)
    if k == 0:
        return []

    _, indices = index.search(query_vector, k)
    results = [chunks[i] for i in indices[0] if i >= 0]
    return results
