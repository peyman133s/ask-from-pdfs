"""Tests for src.generator."""
from __future__ import annotations

import importlib
import json
from unittest.mock import MagicMock, patch

import src.generator as generator_mod
from src.generator import generate


class TestGenerate:
    def test_returns_message_when_no_chunks(self):
        answer, sources = generate("What is this?", [])
        assert "not find" in answer.lower() or "could not" in answer.lower()
        assert sources == []

    def test_returns_answer_and_deduplicated_sources(self, monkeypatch):
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
            with patch.dict("os.environ", {"GAPGPT_API_KEY": "fake-key"}):
                answer, sources = generate("What is this?", chunks)

        assert answer == "The answer."
        assert sources == ["a.pdf", "b.pdf"]  # deduplicated, order preserved

    def test_uses_current_gapgpt_api_endpoint_by_default(self, monkeypatch):
        monkeypatch.delenv("GAPGPT_API_URL", raising=False)
        generator = importlib.reload(generator_mod)
        chunks = [{"filename": "a.pdf", "chunk_index": 0, "text": "Some context."}]

        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps(
            {"answer": "answer"}
        ).encode("utf-8")

        with patch("src.generator.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            with patch.dict("os.environ", {"GAPGPT_API_KEY": "fake-key"}):
                generator.generate("What is this?", chunks)

        request = mock_urlopen.call_args.args[0]
        assert request.full_url == "https://api.gapgpt.app/v1/chat/completions"
        assert request.get_method() == "POST"

    def test_source_order_preserved(self, monkeypatch):
        chunks = [
            {"filename": "z.pdf", "chunk_index": 0, "text": "First."},
            {"filename": "a.pdf", "chunk_index": 0, "text": "Second."},
        ]

        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = json.dumps(
            {"answer": "answer"}
        ).encode("utf-8")

        with patch("src.generator.urllib.request.urlopen", return_value=mock_response):
            with patch.dict("os.environ", {"GAPGPT_API_KEY": "fake-key"}):
                _, sources = generate("q", chunks)

        assert sources == ["z.pdf", "a.pdf"]
