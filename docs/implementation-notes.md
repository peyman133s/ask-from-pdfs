# Implementation Notes

## Suggested Stack

| Layer | Library |
|---|---|
| PDF text extraction | `pypdf` or `pdfminer.six` |
| Text chunking | custom splitter or `langchain` text splitters |
| Embeddings | `sentence-transformers` local embeddings |
| Vector store | FAISS (local file) or Chroma (local persistent) |
| LLM generation | GapGPT API |
| CLI | Python `argparse` or `click` |
| Config | `python-dotenv` + `.env` file |

## Suggested Repo Structure

```
ask-from-pdfs/
├── docs/                   # PRD and planning docs
├── src/
│   ├── __init__.py
│   ├── cli.py              # Entry point: index / ask commands
│   ├── ingest.py           # PDF loading and text extraction
│   ├── chunker.py          # Text chunking logic
│   ├── embedder.py         # Embedding generation
│   ├── vector_store.py     # FAISS / Chroma wrapper
│   ├── retriever.py        # Similarity search
│   └── generator.py        # LLM call and answer formatting
├── data/
│   ├── pdfs/               # Drop PDF files here
│   └── index/              # Auto-generated vector index (git-ignored)
├── tests/
│   └── test_*.py
├── .env.example            # Template for environment variables
├── requirements.txt
├── Dockerfile              # Production image
├── Dockerfile.dev          # Development image
└── .dockerignore
```

## Suggested Milestones

| # | Milestone |
|---|---|
| 1 | Project skeleton, docs, and Docker setup |
| 2 | PDF loading and text extraction (`ingest.py`) |
| 3 | Chunking and embedding pipeline (`chunker.py`, `embedder.py`) |
| 4 | Vector index creation and persistence (`vector_store.py`) |
| 5 | Similarity retrieval (`retriever.py`) |
| 6 | LLM answer generation (`generator.py`) |
| 7 | CLI wiring — `index` and `ask` commands |
| 8 | Source attribution in output |
| 9 | Basic tests and cleanup |

## Agentic Coding Notes
- Keep functions small and composable with clear inputs and outputs.
- Prefer explicit interfaces between ingestion, retrieval, and generation modules.
- Make configuration file-based or environment-based so the agent can change it without touching code.
- Log intermediate steps (`logging` module) so the agent can inspect failures easily.
- Keep the first version simple — avoid premature optimisation.
- Each module should be independently importable and testable.
