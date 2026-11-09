# Acceptance criteria

## Browser walkthrough

Use the [browser setup](../README.md#run-ask-from-files), a configured AvalAI key, and small test documents with distinctive facts.

| Step | Expected result |
|---|---|
| Create a category, upload two files, and assign one to it. | Both rows show **Uploaded**. The other file shows **Uncategorized**. Category and status filters show the matching rows. |
| Select both files and choose **Ingest selected**. | Eligible files are queued. The library updates to **Ready** when indexing completes. |
| Open **Ask a Question** and select the new category. Ask for a fact from its file and open a numbered citation. | The answer is grounded in the selected file. The source shows the filename, excerpt, and page or sheet when available. |
| Move the ready file to a different category and ask again in the original scope. | The original category has no ready files. The moved file is searchable in the destination category without re-ingestion. |
| Upload a corrupt XLSX file and try to ingest it alongside a valid file. | The corrupt file shows **Failed** with a reason and a **Retry** action. The valid file can still become **Ready**. |
| In a disposable workspace, start with an OCR tool unavailable and ingest a scanned PDF. Make the tool available and retry. | The initial failure identifies the missing executable. After restarting with the corrected configuration, retry can bring the file to **Ready**. |
| Restart the backend after indexing. | Files, categories, and ready indexes persist. Work interrupted mid-ingestion is reported as failed and can be retried. |

Also verify upload and ingestion with one file of each supported extension, including both text and scanned PDFs. Try an empty file, an unsupported extension, and a file over 50 MiB to verify upload validation.

## PDF CLI smoke test

1. Follow the [CLI setup](../README.md#pdf-command-line-workflow) and place a text PDF with a known fact in `data/pdfs/`.
2. Run `scripts/local index`. Confirm that it reports the number of chunks indexed.
3. Run `scripts/local ask "What does the document say about the known fact?"`. Confirm that the answer cites the source PDF filename.
4. Point `PDF_DIR` at an empty directory and run the index command. Confirm that it exits with a useful message.
