# ask-from-pdfs

**Author** [@peyman133s](https://github.com/peyman133s)

A local workspace for uploading documents and asking questions with source excerpts. The PDF command-line workflow is also available.

## Run Ask from Files

Use Python 3.10+ and Node.js 20.19 or later in the 20.x series, or Node.js 22.12 or later. Install Tesseract with English and Persian language data for image and scanned PDF OCR, Poppler for scanned PDF rendering, and LibreOffice for legacy DOC files.

On macOS, Homebrew provides the native tools:

```sh
brew install tesseract tesseract-lang poppler
brew install --cask libreoffice
```

If a tool is outside your PATH, set its executable path in `.env` using `SOFFICE_BIN`, `TESSERACT_BIN`, or `PDFTOPPM_BIN`. Use `tesseract --list-langs` to check for `eng` and `fas`. Set `OCR_LANGUAGES=fas` for Persian-only OCR.

```sh
python3 -m venv .venv/web
.venv/web/bin/python -m pip install -r requirements-web.txt
npm --prefix web ci
npm --prefix web run build
test -f .env || cp .env.example .env
```

Set `AVALAI_API_KEY` in the Git-ignored `.env` before asking questions. Set `LLM_MODEL` to a chat model available to your key. The same settings apply to the browser and CLI. Extraction, OCR, and embeddings run locally. AvalAI receives the question and retrieved excerpts for each answer. [AvalAI API reference](https://docs.avalai.org/en/api-reference/introduction)

From the repository root, start the backend:

```sh
.venv/web/bin/python -m uvicorn src.web:app --host 127.0.0.1 --port 8000 --workers 1
```

1. Open the [local workspace](http://127.0.0.1:8000).
2. In **File Library**, select **Upload files**. Add XLS, XLSX, PDF, DOC, DOCX, PNG, JPG, or JPEG files. Assign a category or use **Uncategorized**.
3. Select the uploaded files and choose **Ingest selected**. Wait for **Ready** before asking questions.
4. Open **Ask a Question**, choose a category or **All categories**, and submit a question. Open a numbered citation to inspect the excerpt and its page or sheet when available.

The workspace accepts up to 20 files per upload, each up to 50 MiB. Its originals, SQLite library, and indexes live in `data/workspace/` by default. Keep one server process per workspace directory. A stopped ingestion appears as **Failed** at the next startup and can be retried from the library.

For frontend development, run the API on port 8000 and start `npm --prefix web run dev`. To run the Python tests, install `pytest` and `httpx` in the web virtualenv and run `.venv/web/bin/python -m pytest`.

### Web troubleshooting

| Symptom | What to check |
|---|---|
| The page asks you to build the UI | Run `npm --prefix web ci` and `npm --prefix web run build`, then restart the backend so it can serve `web/dist/`. |
| OCR fails | Check that `tesseract --list-langs` includes the languages in `OCR_LANGUAGES`. Scanned PDFs also require `pdftoppm`. |
| Ingestion shows **Failed** | Read the message in the file row. Fix missing tools or model files, then select **Retry**. For a corrupt or unreadable file, upload a corrected copy. |
| No files are ready in the selected category | Ingest a file in that category or switch to **All categories**. |
| Asking returns a credential or provider error | Check `AVALAI_API_KEY`, `LLM_MODEL`, and `AVALAI_API_URL`. Restart the backend after editing `.env`. |

---

## PDF command-line workflow

1. Ingest a folder of PDFs and extract text
2. Chunk the text and generate embeddings
3. Store embeddings in a local vector index
4. Accept a question from the CLI
5. Retrieve the most relevant chunks
6. Send question + context to an LLM and print a grounded answer with source filenames

---

### CLI implementation map

This project is organized as a small pipeline. The `scripts/local` file is a
helper shell script for local setup and running commands. The actual application
logic is in the Python files under `src/`.

| Pipeline step | User command | Main file and method | Supporting methods | Output |
|---|---|---|---|---|
| Local environment setup | `scripts/local setup` | `scripts/local` -> `setup_venv()` | `ensure_env_file()`, `ensure_data_dirs()` | Creates `.venv`, installs dependencies, creates `.env`, `data/pdfs/`, and `data/index/` |
| Download embedding model | `scripts/local download-embedding-model` | `scripts/local` -> `download_embedding_model()` | `SentenceTransformer(model_repo).save(model_dir)` | Saves the local embedding model in `models/all-MiniLM-L6-v2` |
| Start index command | `scripts/local index` | `scripts/local` -> `run_cli index` -> `src/cli.py` -> `cmd_index()` | Loads `.env`, reads `PDF_DIR`, `INDEX_DIR`, `CHUNK_SIZE`, and `CHUNK_OVERLAP` | Runs the full indexing pipeline |
| Ingest PDFs | Part of `scripts/local index` | `src/ingest.py` -> `load_pdfs()` | `_extract_text()` uses `pypdf.PdfReader` | Returns `Document` objects with `filename` and extracted `text` |
| Chunk text | Part of `scripts/local index` | `src/chunker.py` -> `chunk_documents()` | `chunk_document()` creates overlapping chunks | Returns `Chunk` objects with `filename`, `chunk_index`, and `text` |
| Generate embeddings | Part of `scripts/local index` | `src/embedder.py` -> `embed_chunks()` | `embed_texts()`, `_get_local_model()` | Returns NumPy embedding vectors for every chunk |
| Save vector index | Part of `scripts/local index` | `src/vector_store.py` -> `save()` | Uses `faiss.IndexFlatL2`, `faiss.write_index()`, and JSON metadata | Writes `data/index/index.faiss` and `data/index/chunks.json` |
| Start ask command | `scripts/local ask "question"` | `scripts/local` -> `run_cli ask` -> `src/cli.py` -> `cmd_ask()` | Reads `TOP_K` and `INDEX_DIR` | Runs retrieval and answer generation |
| Retrieve relevant chunks | Part of `scripts/local ask` | `src/retriever.py` -> `retrieve()` | `embedder.embed_query()`, `vector_store.load()`, `vector_store.search()` | Returns the top matching chunk dictionaries |
| Generate final answer | Part of `scripts/local ask` | `src/generator.py` -> `generate()` | `_avalai_chat()` sends the prompt to AvalAI | Prints the answer and source PDF filenames |

### Indexing flow

When you run `scripts/local index`, the flow is:

```text
scripts/local -> run_cli("index")
src/cli.py -> cmd_index()
src/ingest.py -> load_pdfs()
src/chunker.py -> chunk_documents()
src/embedder.py -> embed_chunks()
src/vector_store.py -> save()
```

### Question-answering flow

When you run `scripts/local ask "..."`, the flow is:

```text
scripts/local -> run_cli("ask")
src/cli.py -> cmd_ask()
src/retriever.py -> retrieve()
src/embedder.py -> embed_query()
src/vector_store.py -> load()
src/vector_store.py -> search()
src/generator.py -> generate()
src/generator.py -> _avalai_chat()
```

---

### How to use the CLI

The normal workflow is:

1. Put PDF files in `data/pdfs/`.
2. Build the local vector index with `scripts/local index`.
3. Ask questions with `scripts/local ask "...?"`.
4. Re-run `scripts/local index` whenever you add, remove, or change PDFs.

#### Requirements

- Python 3.10+ for local use
- An AvalAI API key for answer generation
- PDF files with extractable text. Scanned image-only PDFs need OCR first.

#### 1. Set up locally

```bash
git clone https://github.com/peyman133s/ask-from-pdfs.git
cd ask-from-pdfs

scripts/local setup
```

`scripts/local setup` creates `.venv`, installs `requirements.txt`, copies
`.env.example` to `.env` if needed, and creates `data/pdfs/` and `data/index/`.

If you need a different Python package mirror, override `PIP_INDEX_URL` for setup:

```bash
PIP_INDEX_URL=https://mirror-pypi.runflare.com/simple scripts/local setup
```

#### 2. Configure the app

Open `.env` and set your AvalAI key:

```bash
AVALAI_API_KEY=your-avalai-api-key-here
AVALAI_API_URL=https://api.avalai.ir/v1/chat/completions
```

The default `.env.example` values are enough for local paths, chunking, retrieval,
and the local embedding model.

#### 3. Download the embedding model

```bash
scripts/local download-embedding-model
```

This saves `sentence-transformers/all-MiniLM-L6-v2` into
`models/all-MiniLM-L6-v2`. Embeddings run locally and do not require an API key.
After the model exists, `HF_HUB_OFFLINE=1` lets normal indexing avoid Hugging Face
network calls.

If direct Hugging Face access is unavailable, use a compatible mirror for the
download step:

```bash
HF_ENDPOINT=https://hf-mirror.com scripts/local download-embedding-model
```

You can also point `.env` at an existing local model directory:

```bash
LOCAL_EMBEDDING_MODEL=/absolute/path/to/all-MiniLM-L6-v2
HF_HUB_OFFLINE=1
```

#### 4. Add PDFs

Copy your documents into `data/pdfs/`:

```bash
cp /path/to/your-documents/*.pdf data/pdfs/
```

Only files ending in `.pdf` are indexed.

#### 5. Build the index

```bash
scripts/local index
```

This command extracts PDF text, chunks it, embeds the chunks, and writes the FAISS
index to `data/index/`.

Run it again after changing the PDFs.

#### 6. Ask questions

```bash
scripts/local ask "What is this document about?"
scripts/local ask "Which policy limits are mentioned?"
```

The app retrieves the most relevant chunks, sends them with your question to
AvalAI, then prints an answer and the source PDF filenames.

#### Useful local commands

```bash
scripts/local help
scripts/local shell
scripts/local test
```

You can also run the Python CLI directly from an activated environment:

```bash
python -m src.cli index
python -m src.cli ask "What is this document about?"
```

#### Configuration

| Variable | Default or template value | Purpose |
|---|---:|---|
| `PDF_DIR` | `data/pdfs` | Folder scanned for PDFs |
| `INDEX_DIR` | `data/index` | Folder for the CLI's FAISS index |
| `WORKSPACE_DIR` | `data/workspace` | Web originals, SQLite library, and per-file indexes |
| `OCR_LANGUAGES` | `eng+fas` | Tesseract languages for web ingestion |
| `TESSERACT_BIN`, `PDFTOPPM_BIN`, `SOFFICE_BIN` | `tesseract`, `pdftoppm`, `soffice` | Optional executable paths for web ingestion |
| `TESSDATA_PREFIX` | Tesseract's default | Optional directory containing OCR language data |
| `LOCAL_EMBEDDING_MODEL` | `models/all-MiniLM-L6-v2` | Local sentence-transformers model path |
| `HF_HUB_OFFLINE` | `1` | Use local model files only |
| `AVALAI_API_KEY` | required | API key used for answer generation |
| `AVALAI_API_URL` | `https://api.avalai.ir/v1/chat/completions` | Chat completion endpoint |
| `AVALAI_TIMEOUT_SECONDS` | `60` | Chat request timeout in seconds |
| `LLM_MODEL` | `gpt-4o` | Model name sent to AvalAI |
| `CHUNK_SIZE` | `500` | Maximum characters per chunk |
| `CHUNK_OVERLAP` | `50` | Characters shared between adjacent chunks |
| `TOP_K` | `3` | Number of chunks retrieved for each question |

#### Troubleshooting

| Symptom | Fix |
|---|---|
| `No PDF documents found` | Put `.pdf` files in `data/pdfs/`, or set `PDF_DIR` in `.env`. |
| `No text chunks produced` | The PDF may be scanned or image-only. Run OCR first, then index again. |
| `Local embedding model is not available` | Run `scripts/local download-embedding-model`, or set `LOCAL_EMBEDDING_MODEL` to an existing model folder. |
| `Index not found` | Run `scripts/local index` before `scripts/local ask`. |
| AvalAI request error | Check `AVALAI_API_KEY`, `AVALAI_API_URL`, network access, and API quota. |

## Docker usage for the PDF CLI

### Docker Compose

The Docker setup uses Iran-accessible mirrors by default:

- Base images are pulled through ArvanCloud: `docker.arvancloud.ir/python`
- Debian packages use ArvanCloud mirrors
- Python packages use an Iran-accessible PyPI mirror

The production Docker image does not copy `models/` into the image. For Docker
usage, either let the container download the embedding model into the shared
`model_cache` volume on first run, or mount your local `./models` directory.

To let Docker download and cache the model, set these values in `.env` for the
first `index` run:

```bash
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HF_HUB_OFFLINE=0
```

After the first successful container run, you can change `HF_HUB_OFFLINE=1` to
force cache-only model loading.

```bash
test -f .env || cp .env.example .env
# Edit .env and fill in AVALAI_API_KEY.
# For the first Docker model download, also use:
#   LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
#   HF_HUB_OFFLINE=0

mkdir -p data/pdfs data/index
cp your-documents/*.pdf data/pdfs/

docker compose build
docker compose run --rm app python -m src.cli index
docker compose run --rm app python -m src.cli ask "What is this document about?"
```

If you already downloaded the model locally with
`scripts/local download-embedding-model`, keep the default
`LOCAL_EMBEDDING_MODEL=models/all-MiniLM-L6-v2` and mount `./models` when running
the container:

```bash
docker compose run --rm \
  -v "$(pwd)/models:/app/models:ro" \
  app python -m src.cli index
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

### Docker directly

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
├── web/                    # React and TypeScript frontend
├── data/pdfs/              # CLI PDF inputs
├── data/workspace/         # Generated web workspace
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
| [`docs/scaffolding-and-architecture.md`](docs/scaffolding-and-architecture.md) | Architecture, storage, and HTTP API |
| [`docs/implementation-notes.md`](docs/implementation-notes.md) | Stack choices and coding notes |
| [`docs/out-of-scope.md`](docs/out-of-scope.md) | Explicitly out-of-scope items |

---

## License

MIT
