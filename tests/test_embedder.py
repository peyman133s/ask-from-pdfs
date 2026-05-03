"""Tests for src.embedder."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.chunker import Chunk


class TestEmbedTexts:
    def test_returns_empty_array_for_empty_input(self):
        import importlib
        import src.embedder as embedder_mod

        result = embedder_mod.embed_texts([])
        assert result.shape[0] == 0

    def test_local_provider_returns_float32_matrix(self, monkeypatch):
        import src.embedder as embedder_mod

        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)

        monkeypatch.setattr(embedder_mod, "_PROVIDER", "local")
        monkeypatch.setattr(embedder_mod, "_local_model", mock_model)

        result = embedder_mod.embed_texts(["hello"])
        assert result.dtype == np.float32
        assert result.shape == (1, 3)

    def test_unknown_provider_raises(self, monkeypatch):
        import src.embedder as embedder_mod

        monkeypatch.setattr(embedder_mod, "_PROVIDER", "unknown_provider")
        monkeypatch.setattr(embedder_mod, "_local_model", None)

        with pytest.raises(ValueError, match="Unknown EMBEDDING_PROVIDER"):
            embedder_mod.embed_texts(["test"])

    def test_embed_query_returns_1d_vector(self, monkeypatch):
        import src.embedder as embedder_mod

        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.5, 0.6]], dtype=np.float32)

        monkeypatch.setattr(embedder_mod, "_PROVIDER", "local")
        monkeypatch.setattr(embedder_mod, "_local_model", mock_model)

        result = embedder_mod.embed_query("What is this about?")
        assert result.ndim == 1
        assert result.shape == (2,)

    def test_embed_chunks_returns_correct_shape(self, monkeypatch):
        import src.embedder as embedder_mod

        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones((3, 4), dtype=np.float32)

        monkeypatch.setattr(embedder_mod, "_PROVIDER", "local")
        monkeypatch.setattr(embedder_mod, "_local_model", mock_model)

        chunks = [Chunk(filename="f.pdf", chunk_index=i, text=f"text {i}") for i in range(3)]
        result = embedder_mod.embed_chunks(chunks)
        assert result.shape == (3, 4)
