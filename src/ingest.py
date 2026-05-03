"""PDF ingestion: scan a directory for PDF files and extract plain text."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import pypdf

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A single PDF document with its extracted text and source filename."""

    filename: str
    text: str


def load_pdfs(pdf_dir: str | Path) -> list[Document]:
    """Load all PDF files from *pdf_dir* and return a list of :class:`Document`.

    Files that cannot be read are skipped with a warning.
    If the directory is empty or contains no PDFs a warning is logged and an
    empty list is returned — the caller decides how to handle this.
    """
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.is_dir():
        logger.warning("PDF directory does not exist: %s", pdf_dir)
        return []

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in %s", pdf_dir)
        return []

    documents: list[Document] = []
    for path in pdf_files:
        try:
            text = _extract_text(path)
            if not text.strip():
                logger.warning("No text extracted from %s — skipping.", path.name)
                continue
            documents.append(Document(filename=path.name, text=text))
            logger.info("Loaded '%s' (%d chars)", path.name, len(text))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not read '%s': %s — skipping.", path.name, exc)

    return documents


def _extract_text(path: Path) -> str:
    """Return concatenated plain text from all pages of a PDF."""
    reader = pypdf.PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        parts.append(page_text)
    return "\n".join(parts)
