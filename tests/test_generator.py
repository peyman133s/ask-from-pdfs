"""Tests for src.generator."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.generator import ProviderError, generate


class TestGenerate:
    def test_returns_message_when_no_chunks(self):
        answer, sources = generate("What is this?", [])
        assert "not find" in answer.lower() or "could not" in answer.lower()
        assert sources == []

    def test_returns_answer_and_deduplicated_sources(self):
        chunks = [
            {"filename": "a.pdf", "chunk_index": 0, "text": "Some context."},
            {"filename": "b.pdf", "chunk_index": 0, "text": "More context."},
            {"filename": "a.pdf", "chunk_index": 1, "text": "Even more."},
        ]

        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "  The answer.  "}}]}
        ).encode("utf-8")

        with patch("src.generator.urllib.request.urlopen", return_value=mock_response):
            with patch.dict("os.environ", {"AVALAI_API_KEY": "fake-key"}):
                answer, sources = generate("What is this?", chunks)

        assert answer == "The answer."
        assert sources == ["a.pdf", "b.pdf"]  # deduplicated, order preserved

    def test_uses_avalai_endpoint_and_configured_model(self, monkeypatch):
        monkeypatch.delenv("AVALAI_API_URL", raising=False)
        monkeypatch.setenv("AVALAI_API_KEY", "fake-key")
        monkeypatch.setenv("LLM_MODEL", "test-model")
        chunks = [{"filename": "a.pdf", "chunk_index": 0, "text": "Some context."}]

        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "answer"}}]}
        ).encode("utf-8")

        with patch("src.generator.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            generate("What is this?", chunks)

        request = mock_urlopen.call_args.args[0]
        assert request.full_url == "https://api.avalai.ir/v1/chat/completions"
        assert request.get_method() == "POST"
        assert request.get_header("Authorization") == "Bearer fake-key"
        assert json.loads(request.data)["model"] == "test-model"

    def test_source_order_preserved(self):
        chunks = [
            {"filename": "z.pdf", "chunk_index": 0, "text": "First."},
            {"filename": "a.pdf", "chunk_index": 0, "text": "Second."},
        ]

        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "answer"}}]}
        ).encode("utf-8")

        with patch("src.generator.urllib.request.urlopen", return_value=mock_response):
            with patch.dict("os.environ", {"AVALAI_API_KEY": "fake-key"}):
                _, sources = generate("q", chunks)

        assert sources == ["z.pdf", "a.pdf"]

    def test_reports_missing_key(self, monkeypatch):
        monkeypatch.delenv("AVALAI_API_KEY", raising=False)
        with pytest.raises(ProviderError, match="AVALAI_API_KEY"):
            generate("What is this?", [{"filename": "a.pdf", "text": "Context."}])
