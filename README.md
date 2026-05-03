# ask-from-pdfs

A minimal Python starter project for asking questions over PDF documents using a retrieval-augmented generation (RAG) pipeline.

> **Status:** scaffold / starter — ready for agentic coding.

---

## What it does

1. Ingest a folder of PDFs and extract text
2. Chunk the text and generate embeddings
3. Store embeddings in a local vector index
4. Accept a question from the CLI
5. Retrieve the most relevant chunks
6. Send question + context to an LLM and print a grounded answer with source filenames

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/peyman133s/ask-from-pdfs.git
cd ask-from-pdfs

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (if using OpenAI)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add PDFs
cp your-documents/*.pdf data/pdfs/

# 5. Index the PDFs
python -m src.cli index

# 6. Ask a question
python -m src.cli ask "What is this document about?"
```

### Using Docker Compose (recommended)

```bash
# 1. Copy the environment template and fill in your OPENAI_API_KEY
cp .env.example .env

# 2. Add PDFs to the input folder
cp your-documents/*.pdf data/pdfs/

# 3. Build the image
docker compose build

# 4. Index the PDFs
docker compose run --rm app python -m src.cli index

# 5. Ask a question
docker compose run --rm app python -m src.cli ask "What is this document about?"
```

The `data/pdfs/` and `data/index/` directories are bind-mounted from the host, so the
generated vector index persists between runs. Downloaded embedding model weights are
cached in a named Docker volume (`model_cache`) so they are not re-downloaded each time.

**Interactive dev shell** (live-reloads code changes via a volume mount):

```bash
docker compose --profile dev run --rm app-dev
# Inside the container:
python -m src.cli index
python -m src.cli ask "What is this document about?"
```

### Using Docker directly

**Development** (project directory mounted as a volume):
```bash
docker build -f Dockerfile.dev -t ask-from-pdfs-dev .
docker run --rm -it \
  -v "$(pwd)":/app \
  --env-file .env \
  ask-from-pdfs-dev
```

**Production**:
```bash
docker build -t ask-from-pdfs .
docker run --rm \
  -v "$(pwd)/data":/app/data \
  --env-file .env \
  ask-from-pdfs python -m src.cli ask "What is this document about?"
```

---

## Project Structure

```
ask-from-pdfs/
├── docs/                   # PRD and architecture docs
├── src/                    # Application source
├── data/pdfs/              # Drop PDFs here
├── tests/                  # Tests
├── .env.example            # Environment variable template
├── docker-compose.yml      # Compose file (prod + dev profiles)
├── Dockerfile              # Production image
└── Dockerfile.dev          # Development image
```

---

## Documentation

| File | Description |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Product requirements |
| [`docs/requirements.md`](docs/requirements.md) | Functional requirements |
| [`docs/acceptance-criteria.md`](docs/acceptance-criteria.md) | Acceptance criteria |
| [`docs/scaffolding-and-architecture.md`](docs/scaffolding-and-architecture.md) | Architecture and milestone breakdown |
| [`docs/implementation-notes.md`](docs/implementation-notes.md) | Stack choices and coding notes |
| [`docs/out-of-scope.md`](docs/out-of-scope.md) | Explicitly out-of-scope items |

---

## License

MIT
