# Scaffolding and Architecture

## Purpose

`ask-from-pdfs` is a minimal Python starter project that demonstrates a retrieval-augmented generation (RAG) pipeline for asking questions over a local collection of PDF documents.  
It is designed as a clean, agent-friendly scaffold that a developer or coding agent can extend iteratively.

---

## MVP Flow

```
PDFs on disk
    │
    ▼
[1] Ingest  ──► extract raw text from each PDF
    │
    ▼
[2] Chunk   ──► split text into overlapping windows
    │
    ▼
[3] Embed   ──► generate a vector for each chunk
    │
    ▼
[4] Store   ──► persist vectors + metadata in a local index
    │
    ▼  (index time ends here)
    │
    ├─── user types a question ───►
    │
    ▼
[5] Retrieve ──► embed the query, find top-k similar chunks
    │
    ▼
[6] Generate ──► send [question + chunks] to LLM, get answer
    │
    ▼
[7] Output  ──► print answer + source filenames to terminal
```

---

## Recommended Folder Structure

```
ask-from-pdfs/
├── docs/                        # Planning docs (PRD, requirements, architecture)
│   ├── PRD.md
│   ├── requirements.md
│   ├── acceptance-criteria.md
│   ├── out-of-scope.md
│   ├── implementation-notes.md
│   └── scaffolding-and-architecture.md
│
├── src/                         # Application source code
│   ├── __init__.py
│   ├── cli.py                   # CLI entry point (index / ask commands)
│   ├── ingest.py                # PDF loading and text extraction
│   ├── chunker.py               # Text chunking
│   ├── embedder.py              # Embedding generation
│   ├── vector_store.py          # Vector index (FAISS or Chroma)
│   ├── retriever.py             # Similarity search
│   └── generator.py             # LLM call and answer formatting
│
├── data/
│   ├── pdfs/                    # Drop your PDF files here
│   └── index/                   # Auto-generated index (git-ignored)
│
├── tests/
│   └── test_*.py                # Unit and integration tests
│
├── .env.example                 # Template for required environment variables
├── .env                         # Local secrets — never commit this file
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Production image
├── Dockerfile.dev               # Development image (with hot-reload extras)
└── .dockerignore
```

---

## Main Components

### 1. PDF Ingestion (`src/ingest.py`)
- Scans `data/pdfs/` for `.pdf` files.
- Extracts plain text using `pypdf` (or `pdfminer.six`).
- Returns a list of `Document` objects carrying the raw text and filename metadata.
- Skips and warns on unreadable files.

### 2. Chunking (`src/chunker.py`)
- Splits a `Document`'s text into smaller, overlapping windows.
- Default: 500 tokens per chunk, 50-token overlap.
- Returns chunks annotated with `{filename, chunk_index, text}`.

### 3. Embeddings (`src/embedder.py`)
- Converts a list of text chunks into dense vectors.
- Default: local `sentence-transformers` model folder at `models/all-MiniLM-L6-v2`.
- Embeddings run locally with no API key and no server call.
- Run `scripts/local download-embedding-model` once to create the local model folder.

### 4. Vector Store (`src/vector_store.py`)
- Wraps a FAISS flat index (or Chroma persistent store).
- `save(chunks, vectors)` — builds the index and writes it to `data/index/`.
- `load()` — loads the index from disk.
- `search(query_vector, top_k)` — returns top-k chunk records.

### 5. Retrieval (`src/retriever.py`)
- Orchestrates: embed query → vector store search → return chunks.
- Exposes a single `retrieve(question: str, top_k: int) → list[Chunk]` function.

### 6. LLM Generation (`src/generator.py`)
- Builds a prompt from the question and retrieved chunks.
- Calls the configured LLM through GapGPT (default: `gpt-4o`).
- Returns the answer text plus the list of source filenames.

### 7. CLI (`src/cli.py`)
- `python -m src.cli index` — run the ingestion and indexing pipeline.
- `python -m src.cli ask "<question>"` — retrieve and generate an answer.
- Built with `argparse` (or `click`).

---

## Configuration and Environment

All configuration is read from environment variables (loaded from `.env` via `python-dotenv`).

| Variable | Description | Default |
|---|---|---|
| `PDF_DIR` | Folder containing input PDFs | `data/pdfs` |
| `INDEX_DIR` | Folder for the persisted vector index | `data/index` |
| `LOCAL_EMBEDDING_MODEL` | Local sentence-transformers embedding model path | `models/all-MiniLM-L6-v2` |
| `HF_HUB_OFFLINE` | Force local Hugging Face/model loading only | `1` |
| `HF_ENDPOINT` | Optional Hugging Face-compatible model download endpoint | — |
| `GAPGPT_API_KEY` | Required when using GapGPT for LLM answers | — |
| `GAPGPT_API_URL` | GapGPT chat endpoint | `https://api.gapgpt.app/v1/chat/completions` |
| `LLM_MODEL` | LLM model name | `gpt-4o` |
| `CHUNK_SIZE` | Characters (or tokens) per chunk | `500` |
| `CHUNK_OVERLAP` | Overlap between consecutive chunks | `50` |
| `TOP_K` | Number of chunks to retrieve | `3` |

Copy `.env.example` to `.env` and fill in your values before running.

---

## Development Workflow (Agentic Coding)

1. **Read the docs** in `docs/` to understand the scope and plan.
2. **Implement one module at a time**, starting with `ingest.py`.
3. **Run the module in isolation** using a small test script in `tests/`.
4. **Extend the CLI** only after the underlying modules work.
5. **Keep functions pure and small** so they are easy to test and replace.
6. **Use `logging`** (not `print`) for debug output inside modules.
7. **Commit after each working milestone** using the milestone list in `implementation-notes.md`.

---

## Milestone Breakdown

| # | Milestone | Outcome |
|---|---|---|
| 1 | Project skeleton, docs, Docker | Repo ready for coding |
| 2 | PDF ingestion | Can load and extract text from PDFs |
| 3 | Chunking + embedding | Can produce vectors for all chunks |
| 4 | Vector store | Can save and load an index from disk |
| 5 | Retrieval | Can find relevant chunks for a query |
| 6 | LLM generation | Can produce a grounded answer |
| 7 | CLI | End-to-end flow via command line |
| 8 | Tests + polish | Reliable, documented, and clean |
