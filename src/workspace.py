"""Local file library and per-file retrieval indexes for the web application."""
from __future__ import annotations

import heapq
import logging
import os
import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import BinaryIO
from uuid import uuid4

from src import embedder, vector_store
from src.chunker import Chunk, chunk_document
from src.extract import SUPPORTED_EXTENSIONS, ExtractionError, extract_sections
from src.ingest import Document

logger = logging.getLogger(__name__)
UNCATEGORIZED = "uncategorized"
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_UPLOAD_FILES = 20


class WorkspaceError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class LocatedChunk(Chunk):
    location: str | None


class Workspace:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.originals = self.directory / "originals"
        self.indexes = self.directory / "indexes"
        self.embedding_lock = Lock()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with closing(sqlite3.connect(self.directory / "library.sqlite3")) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            with connection:
                yield connection

    def initialize(self) -> None:
        self.originals.mkdir(parents=True, exist_ok=True)
        self.indexes.mkdir(exist_ok=True)
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE
                );
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, extension TEXT NOT NULL,
                    category_id TEXT NOT NULL REFERENCES categories(id),
                    size INTEGER NOT NULL, created_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('uploaded','ingesting','ready','failed')),
                    error TEXT
                );
            """)
            connection.execute(
                "INSERT OR IGNORE INTO categories VALUES (?, ?, ?)",
                (UNCATEGORIZED, "Uncategorized", UNCATEGORIZED),
            )
            connection.execute(
                "UPDATE files SET status = 'failed', error = ? WHERE status = 'ingesting'",
                ("Ingestion was interrupted. Retry to finish indexing this file.",),
            )
        for path in self.indexes.glob(".staging-*"):
            shutil.rmtree(path, ignore_errors=True)

    def categories(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, name FROM categories ORDER BY id != ?, name_key", (UNCATEGORIZED,)
            )
            return [dict(row) for row in rows]

    def add_category(self, name: str) -> dict:
        name = name.strip()
        if not 1 <= len(name) <= 60:
            raise WorkspaceError("Enter a category name between 1 and 60 characters.")
        key = name.casefold()
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO categories VALUES (?, ?, ?) ON CONFLICT(name_key) DO NOTHING",
                (uuid4().hex, name, key),
            )
            return dict(connection.execute(
                "SELECT id, name FROM categories WHERE name_key = ?", (key,)
            ).fetchone())

    def _validate_category(self, category_id: str) -> None:
        with self._connect() as connection:
            if connection.execute("SELECT 1 FROM categories WHERE id = ?", (category_id,)).fetchone() is None:
                raise WorkspaceError("Category not found.", 404)

    def files(self) -> list[dict]:
        with self._connect() as connection:
            return [
                dict(row) for row in connection.execute("SELECT * FROM files ORDER BY created_at DESC, id")
            ]

    def _original(self, file: dict) -> Path:
        return self.originals / f"{file['id']}{file['extension']}"

    def upload(self, inputs: list[tuple[str, BinaryIO, str]]) -> list[dict]:
        if not 1 <= len(inputs) <= MAX_UPLOAD_FILES:
            raise WorkspaceError(f"Upload between 1 and {MAX_UPLOAD_FILES} files at a time.")
        for category_id in {category_id for _, _, category_id in inputs}:
            self._validate_category(category_id)

        records = []
        with TemporaryDirectory(dir=self.originals) as directory:
            staging = Path(directory)
            for name, stream, category_id in inputs:
                name = name.replace("\\", "/").rsplit("/", 1)[-1].strip()
                extension = Path(name).suffix.lower()
                if len(name) > 255 or extension not in SUPPORTED_EXTENSIONS:
                    raise WorkspaceError(f"Unsupported file name or type: {name[:255] or '(unnamed file)'}.", 415)
                file = {
                    "id": uuid4().hex, "name": name, "extension": extension,
                    "category_id": category_id, "created_at": datetime.now(timezone.utc).isoformat(),
                    "size": 0, "status": "uploaded", "error": None,
                }
                with (staging / file["id"]).open("wb") as output:
                    while block := stream.read(1024 * 1024):
                        file["size"] += len(block)
                        if file["size"] > MAX_FILE_BYTES:
                            raise WorkspaceError(f"{name} exceeds the 50 MiB file limit.", 413)
                        output.write(block)
                if not file["size"]:
                    raise WorkspaceError(f"{name} is empty.")
                records.append(file)

            published = []
            try:
                with self._connect() as connection:
                    for file in records:
                        path = self._original(file)
                        (staging / file["id"]).replace(path)
                        published.append(path)
                    connection.executemany("""
                        INSERT INTO files (id, name, extension, category_id, created_at, size, status, error)
                        VALUES (:id, :name, :extension, :category_id, :created_at, :size, :status, :error)
                    """, records)
            except Exception:
                for path in published:
                    path.unlink(missing_ok=True)
                raise
        return records

    def assign_category(self, file_id: str, category_id: str) -> dict:
        self._validate_category(category_id)
        with self._connect() as connection:
            result = connection.execute(
                "UPDATE files SET category_id = ? WHERE id = ?", (category_id, file_id)
            )
            if not result.rowcount:
                raise WorkspaceError("File not found.", 404)
            return dict(connection.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone())

    def claim_ingestion(self, file_ids: list[str]) -> list[dict]:
        """Reserve eligible files in one transaction so overlapping requests cannot duplicate work."""
        claimed = []
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            for file_id in dict.fromkeys(file_ids):
                file = connection.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
                if file is None:
                    raise WorkspaceError("One of the selected files no longer exists.", 404)
                if file["status"] in {"uploaded", "failed"}:
                    connection.execute(
                        "UPDATE files SET status = 'ingesting', error = NULL WHERE id = ?", (file_id,)
                    )
                    claimed.append(dict(file))
        return claimed

    def ingest(self, files: list[dict]) -> None:
        for file in files:
            try:
                self._build_index(file)
                status, error = "ready", None
            except ExtractionError as exc:
                status, error = "failed", str(exc)
            except Exception:
                logger.exception("Ingestion failed for file %s", file["id"])
                status, error = "failed", "Could not read or index this file. Check that it opens, then retry."
            with self._connect() as connection:
                connection.execute(
                    "UPDATE files SET status = ?, error = ? WHERE id = ?", (status, error, file["id"])
                )

    def _build_index(self, file: dict) -> None:
        chunk_size = int(os.getenv("CHUNK_SIZE", "500"))
        overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        if not 0 <= overlap < chunk_size:
            raise ExtractionError("Set CHUNK_SIZE greater than CHUNK_OVERLAP in .env, then retry.")
        chunks: list[Chunk] = []
        size = 0
        for location, text in extract_sections(self._original(file)):
            if not text.strip():
                continue
            size += len(text)
            if size > 2_000_000:
                raise ExtractionError("The extracted text is too large. Split the file into smaller files.")
            chunks.extend(
                LocatedChunk(chunk.filename, chunk.chunk_index, chunk.text, location)
                for chunk in chunk_document(Document(file["name"], text), chunk_size, overlap)
            )
        if not chunks:
            raise ExtractionError("No readable text found. Check the document or upload a clearer image.")

        with self.embedding_lock:
            vectors = embedder.embed_chunks(chunks)
        with TemporaryDirectory(prefix=".staging-", dir=self.indexes) as directory:
            staging = Path(directory) / "index"
            vector_store.save(chunks, vectors, staging)
            destination = self.indexes / file["id"]
            # A previously interrupted attempt may have published the directory without committing Ready.
            if destination.exists():
                shutil.rmtree(destination)
            staging.replace(destination)

    def retrieve(self, question: str, category_id: str | None) -> list[dict]:
        if category_id is not None:
            self._validate_category(category_id)
        with self._connect() as connection:
            sql = "SELECT id FROM files WHERE status = 'ready'"
            if category_id is None:
                rows = connection.execute(sql).fetchall()
            else:
                rows = connection.execute(f"{sql} AND category_id = ?", (category_id,)).fetchall()
        if not rows:
            return []

        with self.embedding_lock:
            vector = embedder.embed_query(question)
        top_k = max(1, int(os.getenv("TOP_K", "3")))
        candidates = []
        for row in rows:
            index, chunks = vector_store.load(self.indexes / row["id"])
            candidates.extend(
                (distance, {**chunk, "file_id": row["id"]})
                for distance, chunk in vector_store.search_with_distances(index, chunks, vector, top_k)
            )
        return [chunk for _, chunk in heapq.nsmallest(top_k, candidates, key=lambda hit: hit[0])]
