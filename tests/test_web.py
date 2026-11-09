"""Web workspace lifecycle and category-scoped retrieval."""
from __future__ import annotations

import io
import json
import sqlite3
import time
from urllib.error import HTTPError

import numpy as np
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("python_multipart")
pytest.importorskip("openpyxl")
pytest.importorskip("xlrd")
pytest.importorskip("docx")

from fastapi.testclient import TestClient
from openpyxl import Workbook

from src import embedder, generator
from src.web import create_app


def _workbook(label: str) -> bytes:
    workbook = Workbook()
    workbook.active.title = "Budget"
    workbook.active.append([label, 18_000])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _wait_for_status(client: TestClient, file_id: str, status: str) -> dict:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        file = next(file for file in client.get("/api/files").json() if file["id"] == file_id)
        if file["status"] == status:
            return file
        time.sleep(0.02)
    pytest.fail(f"Expected {status}, got {file}")


def test_upload_ingest_reassign_and_ask(tmp_path, monkeypatch):
    monkeypatch.setattr(embedder, "embed_chunks", lambda chunks: np.ones((len(chunks), 4), dtype=np.float32))
    monkeypatch.setattr(embedder, "embed_query", lambda question: np.ones(4, dtype=np.float32))
    monkeypatch.setenv("AVALAI_API_KEY", "fake-key")

    def mock_completion(request, timeout):
        assert request.get_header("Authorization") == "Bearer fake-key"
        prompt = json.loads(request.data)["messages"][-1]["content"]
        assert "[1] (source: Budget.xlsx, Sheet: Budget)" in prompt
        assert "Row 1: Travel | 18000" in prompt
        assert "Confidential" not in prompt
        return io.BytesIO(json.dumps({
            "choices": [{"message": {"content": "Travel is $18,000 [1]."}}],
        }).encode())

    monkeypatch.setattr(generator.urllib.request, "urlopen", mock_completion)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        assert not client.post("/api/ask", json={"question": "Budget?"}).json()["sources"]
        finance = client.post("/api/categories", json={"name": "Finance"}).json()["id"]
        assert client.post("/api/categories", json={"name": " finance "}).json()["id"] == finance
        other = client.post("/api/categories", json={"name": "Other"}).json()["id"]
        response = client.post("/api/files", files=[
            ("files", ("Budget.xlsx", _workbook("Travel"))),
            ("files", ("Private.xlsx", _workbook("Confidential"))),
            ("category_ids", (None, finance)),
            ("category_ids", (None, finance)),
        ])
        assert response.status_code == 201
        first, second = response.json()
        assert [first["status"], second["status"]] == ["uploaded", "uploaded"]
        assert not client.post("/api/ask", json={"question": "Budget?", "category_id": finance}).json()["sources"]
        ids = [first["id"], second["id"]]
        assert client.post("/api/ingest", json={"file_ids": [*ids, ids[0]]}).json()["file_ids"] == ids
        for file_id in ids:
            _wait_for_status(client, file_id, "ready")
        assert client.post("/api/ingest", json={"file_ids": ids}).json()["file_ids"] == []
        assert client.patch(f"/api/files/{second['id']}", json={"category_id": other}).status_code == 200

    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        response = client.post("/api/ask", json={"question": "Budget?", "category_id": finance})
        assert response.json() == {
            "answer": "Travel is $18,000 [1].",
            "sources": [{
                "number": 1, "file_id": first["id"], "filename": "Budget.xlsx",
                "location": "Sheet: Budget", "excerpt": "Row 1: Travel | 18000",
            }],
        }

        def rejected(request, timeout):
            raise HTTPError(request.full_url, 401, "Unauthorized", {}, io.BytesIO(b"private upstream detail"))

        monkeypatch.setattr(generator.urllib.request, "urlopen", rejected)
        error = client.post("/api/ask", json={"question": "Budget?", "category_id": finance})
        assert error.status_code == 502
        assert "AvalAI returned HTTP 401" in error.json()["detail"]
        assert "private upstream detail" not in error.text


def test_failed_and_interrupted_ingestion_can_be_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(embedder, "embed_chunks", lambda chunks: np.ones((len(chunks), 4), dtype=np.float32))
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        assert client.post("/api/files", files={"files": ("bad.exe", b"content")}).status_code == 415
        assert client.get("/api/files").json() == []
        file = client.post("/api/files", files={"files": ("bad.xlsx", b"not a spreadsheet")}).json()[0]
        assert file["category_id"] == "uncategorized"
        assert client.post("/api/ingest", json={"file_ids": [file["id"]]}).status_code == 202
        assert "Check that it opens" in _wait_for_status(client, file["id"], "failed")["error"]

    # Simulate an interruption before indexing could finish.
    with sqlite3.connect(tmp_path / "library.sqlite3") as connection:
        connection.execute("UPDATE files SET status = 'ingesting' WHERE id = ?", (file["id"],))
    (tmp_path / "originals" / f"{file['id']}.xlsx").write_bytes(_workbook("Travel"))

    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        assert "interrupted" in client.get("/api/files").json()[0]["error"]
        assert client.post("/api/ingest", json={"file_ids": [file["id"]]}).status_code == 202
        assert _wait_for_status(client, file["id"], "ready")["error"] is None
