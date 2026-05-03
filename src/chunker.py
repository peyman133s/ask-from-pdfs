"""Text chunking: split Document text into overlapping windows."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.ingest import Document

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """A slice of text from a source document."""

    filename: str
    chunk_index: int
    text: str


def chunk_document(
    document: Document,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Split *document* text into overlapping chunks of roughly *chunk_size* characters.

    Args:
        document: Source document.
        chunk_size: Maximum number of characters per chunk.
        chunk_overlap: Number of characters to repeat at the start of each
            successive chunk so that context is not lost at boundaries.

    Returns:
        A list of :class:`Chunk` objects annotated with the source filename.
    """
    text = document.text
    if not text.strip():
        logger.warning("Document '%s' has no text to chunk.", document.filename)
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(Chunk(filename=document.filename, chunk_index=index, text=chunk_text))
            index += 1
        # Move forward by (chunk_size - chunk_overlap) so consecutive chunks share
        # *chunk_overlap* characters of context.
        step = max(1, chunk_size - chunk_overlap)
        start += step

    logger.debug("'%s' → %d chunks", document.filename, len(chunks))
    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[Chunk]:
    """Chunk a list of documents and return all chunks."""
    all_chunks: list[Chunk] = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return all_chunks
