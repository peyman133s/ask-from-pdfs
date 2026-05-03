"""Tests for src.retriever."""
from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from src.retriever import retrieve


class TestRetrieve:
    def test_returns_chunks_from_store(self, tmp_path):
        fake_chunks = [
            {"filename": "a.pdf", "chunk_index": 0, "text": "hello"},
            {"filename": "b.pdf", "chunk_index": 0, "text": "world"},
        ]
        fake_vector = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        with (
            patch("src.retriever.embedder.embed_query", return_value=fake_vector),
            patch("src.retriever.vector_store.load", return_value=(object(), fake_chunks)),
            patch("src.retriever.vector_store.search", return_value=fake_chunks[:1]),
        ):
            results = retrieve("What is this?", top_k=1, index_dir=str(tmp_path))

        assert len(results) == 1
        assert results[0]["filename"] == "a.pdf"

    def test_propagates_file_not_found(self, tmp_path):
        with (
            patch("src.retriever.embedder.embed_query", return_value=np.zeros(3)),
            patch("src.retriever.vector_store.load", side_effect=FileNotFoundError("missing")),
        ):
            with pytest.raises(FileNotFoundError):
                retrieve("question", index_dir=str(tmp_path))
