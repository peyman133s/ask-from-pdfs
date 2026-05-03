# Production Dockerfile
# Lean runtime image — no dev/test dependencies

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install only the system libraries required at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file first to leverage Docker layer caching
COPY requirements.txt ./

# Install Python runtime dependencies only
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/

# Copy environment template (actual .env is mounted or injected at runtime)
COPY .env.example .env.example

# Create the data directories expected by the app
RUN mkdir -p data/pdfs data/index

# Expose a volume so PDFs and the index can be provided from the host
VOLUME ["/app/data"]

# Default command: show usage help
CMD ["python", "-m", "src.cli", "--help"]
