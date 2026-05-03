# Acceptance Criteria

## Indexing
- Given a folder with 3–5 PDFs, the app can build an index successfully.
- The app can report how many chunks were indexed.

## Retrieval
- Given a user question, the app retrieves the top 3 relevant chunks.
- Retrieved chunks include source filename metadata.

## Generation
- The app sends the retrieved chunks and the question to an LLM.
- The app returns a readable answer.

## Output
- The CLI prints the answer.
- The CLI prints the filenames of the source PDFs used for the answer.

## Reliability
- The app handles empty folders gracefully (prints a helpful message and exits cleanly).
- The app handles unreadable or invalid PDFs gracefully (logs a warning and continues).
- The app does not crash on ordinary user input errors.

## Minimal Demo Scenario
1. Put a few PDFs in the `data/pdfs/` folder.
2. Run: `python -m src.cli index`
3. Ask a question: `python -m src.cli ask "What is this document about?"`
4. See a grounded answer with source filenames printed to the terminal.
