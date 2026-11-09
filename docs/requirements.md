# Functional requirements

## File library and ingestion

- Accept XLS, XLSX, PDF, DOC, DOCX, PNG, JPG, and JPEG uploads. Enforce 1–20 files per upload, a 50 MiB limit per file, and a supported filename extension.
- Assign one category per file. Default to **Uncategorized**, allow category creation and reassignment, and filter the library by category or ingestion status.
- Store original files and metadata locally. Queue up to 20 file IDs per ingestion request and process jobs sequentially. Persist **Uploaded**, **Ingesting**, **Ready**, and **Failed** states.
- Extract text from supported documents and spreadsheets. Use OCR for images and PDF pages with no extractable text. Preserve page numbers and sheet names where available.
- Reject ingestion when extraction produces no readable text or exceeds two million characters per file. Display a failure reason and offer retry. Mark interrupted work as failed on the next startup.

## Questions and sources

- Accept a nonblank question of up to 4,000 characters. Search ready files across the workspace or in the selected category.
- Embed the question locally and retrieve up to `TOP_K` matching chunks, with a default of three. Send the question and retrieved excerpts to AvalAI for a grounded answer.
- Return numbered excerpts with source filenames and available locations. Show an empty-scope message when there are no ready files and show actionable provider errors.

## PDF CLI

- Index text PDFs from the configured input directory. Skip unreadable or textless PDFs with a warning.
- Generate local embeddings and persist a separate FAISS index. Print answers and deduplicated source filenames to the terminal.

See the [architecture](scaffolding-and-architecture.md) for storage and API details.
