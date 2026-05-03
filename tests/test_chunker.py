"""Tests for src.chunker."""
from __future__ import annotations

from src.chunker import Chunk, chunk_document, chunk_documents
from src.ingest import Document


def _make_doc(text: str, filename: str = "test.pdf") -> Document:
    return Document(filename=filename, text=text)


class TestChunkDocument:
    def test_empty_text_returns_no_chunks(self):
        doc = _make_doc("   ")
        assert chunk_document(doc) == []

    def test_short_text_single_chunk(self):
        doc = _make_doc("Hello world")
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world"
        assert chunks[0].filename == "test.pdf"
        assert chunks[0].chunk_index == 0

    def test_long_text_multiple_chunks(self):
        # 1000-char text, chunk_size=300, overlap=50 → step=250 → 4 chunks
        text = "A" * 1000
        chunks = chunk_document(_make_doc(text), chunk_size=300, chunk_overlap=50)
        assert len(chunks) >= 3

    def test_overlap_means_repeated_content(self):
        text = "0123456789" * 10  # 100 chars
        chunks = chunk_document(_make_doc(text), chunk_size=20, chunk_overlap=5)
        # The last 5 chars of chunk N should appear at the start of chunk N+1.
        for i in range(len(chunks) - 1):
            tail = chunks[i].text[-5:]
            head = chunks[i + 1].text[:5]
            assert tail == head, f"Overlap mismatch between chunk {i} and {i+1}"

    def test_chunk_index_increments(self):
        text = "word " * 300
        chunks = chunk_document(_make_doc(text), chunk_size=50, chunk_overlap=10)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_filename_preserved(self):
        doc = _make_doc("Some text.", filename="my_doc.pdf")
        chunks = chunk_document(doc, chunk_size=100)
        assert all(c.filename == "my_doc.pdf" for c in chunks)


class TestChunkDocuments:
    def test_combines_chunks_from_multiple_docs(self):
        docs = [_make_doc("AAA " * 200, "a.pdf"), _make_doc("BBB " * 200, "b.pdf")]
        chunks = chunk_documents(docs, chunk_size=100, chunk_overlap=10)
        filenames = {c.filename for c in chunks}
        assert "a.pdf" in filenames
        assert "b.pdf" in filenames
