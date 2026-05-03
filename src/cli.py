"""CLI entry point for ask-from-pdfs.

Commands
--------
python -m src.cli index
    Ingest PDFs, chunk, embed, and save the vector index.

python -m src.cli ask "<question>"
    Retrieve relevant chunks and generate an answer.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "WARNING"),
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_PDF_DIR = os.getenv("PDF_DIR", "data/pdfs")
_INDEX_DIR = os.getenv("INDEX_DIR", "data/index")
_CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
_CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
_TOP_K = int(os.getenv("TOP_K", "3"))


def cmd_index(_args: argparse.Namespace) -> int:
    """Run the full ingestion and indexing pipeline."""
    from src import embedder, vector_store  # noqa: PLC0415
    from src.chunker import chunk_documents  # noqa: PLC0415
    from src.ingest import load_pdfs  # noqa: PLC0415

    print(f"Loading PDFs from '{_PDF_DIR}' …")
    documents = load_pdfs(_PDF_DIR)
    if not documents:
        print("No PDF documents found. Add PDF files to the data/pdfs/ folder and try again.")
        return 1

    print(f"Loaded {len(documents)} document(s): {[d.filename for d in documents]}")

    print("Chunking documents …")
    chunks = chunk_documents(documents, chunk_size=_CHUNK_SIZE, chunk_overlap=_CHUNK_OVERLAP)
    if not chunks:
        print("No text chunks produced. Check that the PDFs contain extractable text.")
        return 1
    print(f"Created {len(chunks)} chunk(s).")

    print("Generating embeddings (this may take a moment) …")
    vectors = embedder.embed_chunks(chunks)

    print(f"Saving index to '{_INDEX_DIR}' …")
    vector_store.save(chunks, vectors, _INDEX_DIR)

    print(f"Done! Indexed {len(chunks)} chunks from {len(documents)} document(s).")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    """Retrieve relevant chunks and generate an answer."""
    question = args.question.strip()
    if not question:
        print("Please provide a non-empty question.")
        return 1

    from src import generator, retriever  # noqa: PLC0415

    try:
        chunks = retriever.retrieve(question, top_k=_TOP_K, index_dir=_INDEX_DIR)
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1

    if not chunks:
        print("No relevant context found for your question.")
        return 1

    print("Generating answer …\n")
    try:
        answer, sources = generator.generate(question, chunks)
    except Exception as exc:  # noqa: BLE001
        print(f"Error while generating answer: {exc}")
        return 1

    print("Answer:")
    print(answer)
    print()
    print("Sources:")
    for src in sources:
        print(f"  • {src}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="src.cli",
        description="Ask questions about a local collection of PDF documents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="Ingest PDFs and build the vector index.")

    ask_parser = sub.add_parser("ask", help="Ask a question against the indexed PDFs.")
    ask_parser.add_argument("question", help="The question to answer.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "index":
        return cmd_index(args)
    if args.command == "ask":
        return cmd_ask(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
