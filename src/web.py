"""FastAPI entry point for the single-user local document workspace."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

load_dotenv()

from src import generator  # noqa: E402
from src.workspace import MAX_UPLOAD_FILES, UNCATEGORIZED, Workspace, WorkspaceError  # noqa: E402

FRONTEND = Path(__file__).resolve().parents[1] / "web" / "dist"


class CategoryInput(BaseModel):
    name: str


class AssignmentInput(BaseModel):
    category_id: str


class IngestionInput(BaseModel):
    file_ids: list[str] = Field(min_length=1, max_length=MAX_UPLOAD_FILES)


class QuestionInput(BaseModel):
    question: str = Field(max_length=4_000)
    category_id: str | None = None


def create_app(workspace_dir: Path | None = None) -> FastAPI:
    workspace = Workspace(workspace_dir or Path(os.getenv("WORKSPACE_DIR", "data/workspace")))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        workspace.initialize()
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="ingestion") as worker:
            app.state.worker = worker
            yield

    app = FastAPI(title="Ask from Files", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.middleware("http")
    async def restrict_cross_origin_writes(request: Request, call_next):
        origin = request.headers.get("origin")
        if origin and request.method in {"POST", "PATCH"}:
            if origin != f"{request.url.scheme}://{request.url.netloc}":
                return JSONResponse({"detail": "Open the local workspace to make this request."}, status_code=403)
        return await call_next(request)

    @app.exception_handler(WorkspaceError)
    async def workspace_error(_request: Request, exc: WorkspaceError):
        return JSONResponse({"detail": str(exc)}, status_code=exc.status_code)

    @app.get("/api/categories")
    def list_categories():
        return workspace.categories()

    @app.post("/api/categories", status_code=201)
    def add_category(body: CategoryInput):
        return workspace.add_category(body.name)

    @app.get("/api/files")
    def list_files():
        return workspace.files()

    @app.post("/api/files", status_code=201)
    def upload_files(
        files: Annotated[list[UploadFile], File()],
        category_ids: Annotated[list[str] | None, Form()] = None,
    ):
        if category_ids is None:
            category_ids = [UNCATEGORIZED] * len(files)
        if len(category_ids) != len(files):
            raise HTTPException(422, "Choose one category for each uploaded file.")
        return workspace.upload([
            (file.filename or "", file.file, category_id)
            for file, category_id in zip(files, category_ids)
        ])

    @app.patch("/api/files/{file_id}")
    def assign_category(file_id: str, body: AssignmentInput):
        return workspace.assign_category(file_id, body.category_id)

    @app.post("/api/ingest", status_code=202)
    def queue_ingestion(body: IngestionInput, request: Request):
        files = workspace.claim_ingestion(body.file_ids)
        if files:
            request.app.state.worker.submit(workspace.ingest, files)
        return {"file_ids": [file["id"] for file in files]}

    @app.post("/api/ask")
    def ask(body: QuestionInput):
        question = body.question.strip()
        if not question:
            raise HTTPException(422, "Enter a question.")
        chunks = workspace.retrieve(question, body.category_id)
        if not chunks:
            return {"answer": "No ready files in this scope. Ingest files or choose another category.", "sources": []}
        try:
            answer = generator.answer_question(question, chunks)
        except generator.ProviderError as exc:
            raise HTTPException(502, str(exc)) from exc
        return {
            "answer": answer,
            "sources": [
                {
                    "number": number, "file_id": chunk["file_id"], "filename": chunk["filename"],
                    "location": chunk["location"], "excerpt": chunk["text"],
                }
                for number, chunk in enumerate(chunks, start=1)
            ],
        }

    if FRONTEND.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="web")
    else:
        @app.get("/", response_class=PlainTextResponse)
        def build_frontend():
            return "Build the UI with: npm --prefix web ci && npm --prefix web run build"

    return app


app = create_app()
