# Ask from Files product requirements

## Overview

Ask from Files is a single-user local workspace for asking questions about documents. Users upload files, organize them into categories, and choose when to ingest them. The answer view shows the source excerpts used for retrieval. A separate PDF command-line workflow supports terminal users.

## Browser workflow

1. Upload XLS, XLSX, PDF, DOC, DOCX, PNG, JPG, or JPEG files. An upload can contain up to 20 files of up to 50 MiB each.
2. Assign one category per file. Files without a selection start in **Uncategorized**. Categories can be created during upload or from the library.
3. Select files and choose **Ingest selected**. Track progress in the library and retry failures after fixing the cause.
4. Ask a question across all ready files or within one category. Use numbered citations to inspect excerpts, including a PDF page or spreadsheet sheet when available.

## Success criteria

- Users can tell which files are uploaded, ingesting, ready, or failed, and can act on an ingestion error.
- Category changes affect the next question without re-ingestion. Uploaded, ingesting, and failed files stay outside retrieval.
- The workspace retains files, categories, and ready indexes across server restarts.
- The CLI indexes text PDFs from a folder and prints an answer with source filenames.

Extraction, OCR, indexing, and retrieval run locally. AvalAI generates answers from the question and retrieved excerpts. See the [requirements](requirements.md), [acceptance walkthrough](acceptance-criteria.md), and [scope boundaries](out-of-scope.md).
