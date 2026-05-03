# Product Requirements Document (PRD)

## Project: ask-from-pdfs

### Overview
Build a minimal Python retrieval-augmented generation (RAG) application that lets a user ask questions about a small set of PDF documents from the command line.

The project is intended as a small, agent-friendly starter repo for iterative coding. It should demonstrate the core RAG loop:
1. Ingest PDFs
2. Extract text
3. Chunk text
4. Embed chunks
5. Store embeddings in a vector index
6. Retrieve top matches for a query
7. Send retrieved context to an LLM
8. Print the answer with source filenames

### Goals
- Provide a simple end-to-end RAG prototype in Python.
- Keep the project easy for an agentic coding workflow to understand and modify.
- Support a basic CLI workflow with minimal setup.
- Show source filenames alongside generated answers.

### Success Criteria
- A user can place 3–5 PDFs in an input folder.
- The system can index those PDFs into a vector store.
- A user can ask a question from the CLI.
- The system retrieves relevant text chunks.
- The system sends retrieved context to an LLM.
- The system prints a grounded answer and source filenames.

### Users
- **Primary:** developer exploring RAG fundamentals.
- **Secondary:** coding agent or automation workflow maintaining the repo.

### Assumptions
- PDFs are text-based and do not require OCR.
- The dataset is small (a few documents).
- The application runs locally in Python.
- The repo is intentionally minimal and not production-ready.

### Example User Flow
1. User adds PDF files to an input directory.
2. User runs an indexing command.
3. The app extracts and chunks text from PDFs.
4. The app stores embeddings in FAISS or Chroma.
5. User enters a question in the CLI.
6. The app retrieves the top 3 chunks.
7. The app sends the chunks and question to an LLM.
8. The app prints the answer and source filenames.

### Out of Scope
- Web UI
- Authentication
- Multi-user support
- Advanced reranking
- Distributed indexing
- OCR for scanned PDFs
- Production deployment

### Non-Functional Requirements
- The code should be easy to read and modular.
- The project should be understandable from the README and docs alone.
- The indexing and querying flow should be deterministic where possible.
- Errors should be handled with clear CLI messages.

### Deliverables
- CLI-based RAG prototype
- PDF ingestion and indexing pipeline
- Query flow with retrieval and generation
- Source attribution in output
- Documentation for setup and usage

### Open Questions
- Which LLM provider should be used by default?
- Should the first implementation use FAISS or Chroma?
- Should embeddings be local (sentence-transformers) or hosted (OpenAI)?
