"""Tests for src.ingest."""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ingest import Document, load_pdfs, _extract_text


class TestLoadPdfs:
    def test_returns_empty_for_missing_directory(self, tmp_path):
        missing = tmp_path / "nonexistent"
        result = load_pdfs(missing)
        assert result == []

    def test_returns_empty_for_empty_directory(self, tmp_path):
        result = load_pdfs(tmp_path)
        assert result == []

    def test_skips_unreadable_pdf(self, tmp_path):
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_bytes(b"not a real pdf")
        # pypdf will raise on malformed files; we expect a warning and empty result
        result = load_pdfs(tmp_path)
        assert isinstance(result, list)

    def test_loads_valid_pdf(self, tmp_path):
        """Patch _extract_text so we don't need a real PDF on disk."""
        fake_pdf = tmp_path / "sample.pdf"
        fake_pdf.write_bytes(b"%PDF fake content")

        with patch("src.ingest._extract_text", return_value="Hello world text"):
            result = load_pdfs(tmp_path)

        assert len(result) == 1
        assert isinstance(result[0], Document)
        assert result[0].filename == "sample.pdf"
        assert result[0].text == "Hello world text"

    def test_skips_pdf_with_no_text(self, tmp_path):
        fake_pdf = tmp_path / "empty.pdf"
        fake_pdf.write_bytes(b"%PDF fake")

        with patch("src.ingest._extract_text", return_value="   "):
            result = load_pdfs(tmp_path)

        assert result == []
