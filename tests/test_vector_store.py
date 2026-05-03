"""Tests for src.vector_store."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from src.chunker import Chunk
from src.vector_store import save, load, search


def _make_chunks(n: int) -> list[Chunk]:
    return [Chunk(filename=f"doc{i}.pdf", chunk_index=0, text=f"text {i}") for i in range(n)]


def _make_vectors(n: int, dim: int = 8) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.random((n, dim)).astype(np.float32)


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path):
        chunks = _make_chunks(5)
        vectors = _make_vectors(5)

        save(chunks, vectors, tmp_path)

        index, loaded_chunks = load(tmp_path)
        assert index.ntotal == 5
        assert len(loaded_chunks) == 5
        assert loaded_chunks[0]["filename"] == "doc0.pdf"

    def test_load_raises_when_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load(tmp_path / "nonexistent")


class TestSearch:
    def test_returns_top_k_results(self, tmp_path):
        chunks = _make_chunks(10)
        vectors = _make_vectors(10)

        save(chunks, vectors, tmp_path)
        index, loaded_chunks = load(tmp_path)

        query = vectors[0]  # exact match should be ranked first
        results = search(index, loaded_chunks, query, top_k=3)
        assert len(results) == 3
        # The first result should be the same chunk as the query vector
        assert results[0]["filename"] == "doc0.pdf"

    def test_top_k_capped_at_total(self, tmp_path):
        chunks = _make_chunks(2)
        vectors = _make_vectors(2)

        save(chunks, vectors, tmp_path)
        index, loaded_chunks = load(tmp_path)

        results = search(index, loaded_chunks, vectors[0], top_k=100)
        assert len(results) == 2

    def test_empty_index_returns_empty(self, tmp_path):
        chunks = _make_chunks(3)
        vectors = _make_vectors(3)

        save(chunks, vectors, tmp_path)
        index, loaded_chunks = load(tmp_path)

        # Build an empty index of the same dimension
        import faiss

        empty_index = faiss.IndexFlatL2(8)
        results = search(empty_index, [], vectors[0], top_k=3)
        assert results == []
