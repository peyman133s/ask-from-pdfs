"""Tests for src.generator."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

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
        mock_response.choices[0].message.content = "  The answer.  "

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("src.generator.OpenAI", return_value=mock_client):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "fake-key"}):
                answer, sources = generate("What is this?", chunks)

        assert answer == "The answer."
        assert sources == ["a.pdf", "b.pdf"]  # deduplicated, order preserved

    def test_source_order_preserved(self, monkeypatch):
        chunks = [
            {"filename": "z.pdf", "chunk_index": 0, "text": "First."},
            {"filename": "a.pdf", "chunk_index": 0, "text": "Second."},
        ]

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "answer"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("src.generator.OpenAI", return_value=mock_client):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "fake-key"}):
                _, sources = generate("q", chunks)

        assert sources == ["z.pdf", "a.pdf"]
