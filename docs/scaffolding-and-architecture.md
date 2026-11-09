# Architecture

## Browser workspace

The React and TypeScript UI in `web/` uses a same-origin FastAPI API in `src/web.py`. Vite builds the browser assets into `web/dist/`, which FastAPI serves at startup. The local development proxy forwards `/api` to port 8000.

The web workspace uses one server process and one ingestion worker per `WORKSPACE_DIR` (default `data/workspace/`). SQLite stores file records, categories, and status in `library.sqlite3`. Uploaded originals live in `originals/` under generated IDs, and each ready file has a FAISS index and chunk metadata under `indexes/<file_id>/`.

## Ingestion and retrieval

1. Uploading stores the original and creates an **Uploaded** record. Explicit ingestion claims eligible files and marks them **Ingesting**.
2. The worker extracts text and source locations, then splits the text into overlapping character windows and generates local sentence-transformer embeddings.
3. The worker builds the file index in a staging directory, publishes it, and marks the file **Ready**. Failures store a message and mark the file **Failed**. Retry claims the file again. On startup, the API marks interrupted jobs as failed and clears stale index staging directories.
4. A question selects ready files in the requested scope and embeds the query once. The backend merges per-file FAISS results by squared L2 distance and takes the closest `TOP_K` chunks. Category assignment changes the search scope immediately because the API reads categories from SQLite at query time.
5. AvalAI receives the question and numbered excerpts, including filenames and available locations. The API returns the generated answer and those excerpts. Extraction, OCR, embeddings, and retrieval run locally.

## HTTP API

| Method and path | Request and result |
|---|---|
| `GET /api/categories` | List categories, including **Uncategorized**. |
| `POST /api/categories` | Accept a JSON `name` and return its category ID and name. |
| `GET /api/files` | List uploaded file records with category, ingestion status, and error details. |
| `POST /api/files` | Accept multipart `files` and optional repeated `category_ids` in matching order. Return the uploaded records. |
| `PATCH /api/files/{file_id}` | Accept a JSON `category_id` and return the updated file record. |
| `POST /api/ingest` | Accept JSON `file_ids` and return the IDs queued for ingestion with HTTP 202. |
| `POST /api/ask` | Accept JSON `question` and optional `category_id`. Return `answer` and numbered `sources`, each with a file ID, filename, location when available, and excerpt. An omitted or null category searches all ready files. |

The running server exposes interactive API documentation at [`/docs`](http://127.0.0.1:8000/docs).

## PDF CLI

The CLI reads text PDFs from `PDF_DIR` (default `data/pdfs/`) and writes its FAISS index and chunk metadata to `INDEX_DIR` (default `data/index/`). The CLI and browser use separate corpora and share the chunking, embedding, FAISS, and AvalAI generation code. See the [README](../README.md#pdf-command-line-workflow) for setup and commands.
