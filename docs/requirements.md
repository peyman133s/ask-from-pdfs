# Requirements

## Functional Requirements

### PDF Ingestion
- The system must read PDF files from a configured input folder.
- The system must extract text from each PDF.
- The system must ignore unsupported or empty files gracefully.

### Chunking
- The system must split extracted text into smaller chunks.
- The chunking strategy must be simple and configurable (e.g. chunk size, overlap).

### Embeddings and Indexing
- The system must generate embeddings for each chunk.
- The system must store embeddings in a vector index.
- The vector index must support similarity search.

### Querying
- The system must accept a user question from the CLI.
- The system must retrieve the top 3 most relevant chunks.
- The system must pass the question and retrieved chunks to an LLM.
- The system must return a natural-language answer.

### Output
- The system must print the answer in the CLI.
- The system must display source filenames for the retrieved chunks.

## Data Requirements
- Input documents must be PDF files.
- Metadata should include at least:
  - Filename
  - Chunk index
  - Optional page number if available

## Quality Requirements
- The answer should be grounded in retrieved context.
- If relevant context is missing, the system should say so clearly.
- The CLI should provide helpful error messages.

## Implementation Constraints
- Use Python 3.10+.
- Keep dependencies minimal.
- Prefer a local-first development experience.
- Design the code so it can be extended later.
- Configuration via environment variables or a `.env` file.
