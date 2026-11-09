# Implementation notes

## Extraction tools

| Input | Extraction | Source location |
|---|---|---|
| PDF | pypdf extracts text per page. Poppler renders pages without text for Tesseract OCR. | Page |
| XLS | xlrd reads cell values and serializes rows as text. | Sheet |
| XLSX | openpyxl reads stored cell values in read-only mode. Formula cells depend on cached results. | Sheet |
| DOCX | python-docx reads paragraphs and table cells. | Filename |
| DOC | Headless LibreOffice converts the original to DOCX in a temporary directory. | Filename |
| PNG, JPG, JPEG | Tesseract extracts visible text. | Filename |

The web worker defaults to Tesseract languages `eng+fas`. For executable and language-data overrides, see the [environment template](../.env.example). The PDF CLI uses pypdf for text extraction. For scanned PDFs in the CLI workflow, run OCR before indexing.

## Running and changing the project

- Run the web backend with a single Uvicorn worker. The ingestion queue runs in the same process. The library polls file status through `GET /api/files`.
- Set `LOCAL_EMBEDDING_MODEL` to a local sentence-transformer directory for offline embeddings. If you switch embedding models, rebuild the CLI index and re-upload and ingest the affected files in a fresh web workspace so stored and query vectors use the same model.
- Keep `AVALAI_API_KEY` in a local server environment or Git-ignored `.env`. `LLM_MODEL`, `AVALAI_API_URL`, and `AVALAI_TIMEOUT_SECONDS` configure both clients. The API uses the credential when calling AvalAI.
- Use [the README](../README.md#run-ask-from-files) to install and build, and the [acceptance walkthrough](acceptance-criteria.md) to verify both entry points.
