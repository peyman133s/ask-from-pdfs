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

# 2. Create a local virtualenv and install dependencies
scripts/local setup

# 3. Download the embedding model once into ./models
scripts/local download-embedding-model

# 4. Edit .env and add your GAPGPT_API_KEY
#    Keep GAPGPT_API_URL at https://api.gapgpt.app/v1/chat/completions

# 5. Add PDFs
cp your-documents/*.pdf data/pdfs/

# 6. Index the PDFs
scripts/local index

# 7. Ask a question
scripts/local ask "What is this document about?"
```

The local script avoids Docker builds completely. It creates `.venv`, copies
`.env.example` to `.env` if needed, creates `data/pdfs/` and `data/index/`, and
runs the existing Python CLI from your host machine.

If you need a different Python package mirror, override `PIP_INDEX_URL` only for
local setup:

```bash
PIP_INDEX_URL=https://mirror-pypi.runflare.com/simple scripts/local setup
```

Other useful local commands:

```bash
scripts/local download-embedding-model
scripts/local shell
scripts/local test
```

### Local embeddings

Embeddings use `sentence-transformers` locally and do not require an API key. The
project is configured to load the model from `models/all-MiniLM-L6-v2` with
`HF_HUB_OFFLINE=1`, so normal indexing does not contact Hugging Face after the model
folder exists.

Download the model once:

```bash
scripts/local download-embedding-model
```

If direct Hugging Face access is unavailable from Iran, set a Hugging Face-compatible
mirror/proxy for the download step:

```bash
HF_ENDPOINT=https://hf-mirror.com scripts/local download-embedding-model
```

You can also copy an already-downloaded `sentence-transformers` model folder into
`models/all-MiniLM-L6-v2`, or point `.env` at another local folder:

```bash
LOCAL_EMBEDDING_MODEL=/absolute/path/to/all-MiniLM-L6-v2
HF_HUB_OFFLINE=1
```

### Using Docker Compose

The Docker setup uses Iran-accessible mirrors by default:

- Base images are pulled through ArvanCloud: `docker.arvancloud.ir/python`
- Debian packages use ArvanCloud mirrors
- Python packages use an Iran-accessible PyPI mirror

```bash
# 1. Copy the environment template and fill in your GAPGPT_API_KEY
#    Keep GAPGPT_API_URL at https://api.gapgpt.app/v1/chat/completions
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

If a mirror is stale or unavailable, override it at build time:

```bash
DEBIAN_MIRROR=http://mirror.arvancloud.ir/debian \
DEBIAN_SECURITY_MIRROR=http://mirror.arvancloud.ir/debian-security \
PIP_INDEX_URL=https://mirror-pypi.runflare.com/simple \
docker compose build
```

The `data/pdfs/` and `data/index/` directories are bind-mounted from the host, so the
generated vector index persists between runs. Downloaded embedding model weights are
cached in a named Docker volume (`model_cache`) so they are not re-downloaded each time.
After the first successful model download, set `HF_HUB_OFFLINE=1` in `.env` to use the
cached model only and avoid Hugging Face startup `HEAD` requests that can time out on
slow or restricted connections.

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

**Using a ready image**:

If you publish this app image to an ArvanCloud Container Registry, you can skip local
Dockerfile builds and point Compose at that image instead:

```yaml
services:
  app:
    image: <your-arvan-registry>/<namespace>/ask-from-pdfs:latest
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
