"""Extract searchable sections from the web workspace's supported file formats."""
from __future__ import annotations

import os
import subprocess
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document as WordDocument
from openpyxl import load_workbook
from pypdf import PdfReader
import xlrd

SUPPORTED_EXTENSIONS = frozenset({".xls", ".xlsx", ".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"})


class ExtractionError(ValueError):
    """An extraction failure that can be explained to the user."""


def _run_tool(variable: str, binary: str, args: list[str], failure: str) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [os.getenv(variable, binary), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=True,
        )
    except FileNotFoundError as exc:
        raise ExtractionError(f"Install {binary} or set {variable}, then retry ingestion.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ExtractionError(f"{binary} timed out. Try a smaller file.") from exc
    except subprocess.CalledProcessError as exc:
        raise ExtractionError(failure) from exc
    return result


def _ocr(path: Path) -> str:
    languages = os.getenv("OCR_LANGUAGES", "eng+fas")
    failure = f"OCR failed. Check the image and install the Tesseract language data for {languages}."
    result = _run_tool(
        "TESSERACT_BIN", "tesseract", [str(path), "stdout", "-l", languages],
        failure,
    )
    if "Failed loading language" in result.stderr:
        raise ExtractionError(failure)
    return result.stdout


def _pdf_sections(path: Path) -> Iterator[tuple[str, str]]:
    reader = PdfReader(path)
    if reader.is_encrypted and not reader.decrypt(""):
        raise ExtractionError("Remove the PDF password before uploading the file.")
    with TemporaryDirectory() as directory:
        image = Path(directory) / "page"
        for number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                _run_tool(
                    "PDFTOPPM_BIN", "pdftoppm",
                    ["-f", str(number), "-l", str(number), "-scale-to", "2200",
                     "-singlefile", "-png", str(path), str(image)],
                    f"Could not render page {number} for OCR. Check that the PDF opens correctly.",
                )
                text = _ocr(image.with_suffix(".png"))
            yield f"Page {number}", text


def _sheet_text(rows) -> str:
    lines = []
    size = 0
    for number, row in enumerate(rows, start=1):
        cells = ["" if value is None else str(value) for value in row]
        while cells and not cells[-1]:
            cells.pop()
        if cells:
            line = f"Row {number}: " + " | ".join(cells)
            size += len(line)
            if size > 2_000_000:
                raise ExtractionError("This sheet is too large to ingest. Split it into smaller sheets.")
            lines.append(line)
    return "\n".join(lines)


def _xlsx_sections(path: Path) -> Iterator[tuple[str, str]]:
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        for sheet in book.worksheets:
            yield f"Sheet: {sheet.title}", _sheet_text(sheet.values)
    finally:
        book.close()


def _xls_sections(path: Path) -> Iterator[tuple[str, str]]:
    book = xlrd.open_workbook(str(path), on_demand=True)
    try:
        for name in book.sheet_names():
            sheet = book.sheet_by_name(name)
            yield f"Sheet: {name}", _sheet_text(sheet.row_values(i) for i in range(sheet.nrows))
            book.unload_sheet(name)
    finally:
        book.release_resources()


def _docx_text(path: Path) -> str:
    document = WordDocument(path)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        paragraphs.extend(" | ".join(cell.text for cell in row.cells) for row in table.rows)
    return "\n".join(paragraphs)


def _doc_text(path: Path) -> str:
    with TemporaryDirectory() as directory:
        output = Path(directory)
        _run_tool(
            "SOFFICE_BIN", "soffice",
            [f"-env:UserInstallation={(output / 'profile').as_uri()}",
             "--headless", "--convert-to", "docx", "--outdir", str(output), str(path)],
            "Could not open the DOC file. Check that it opens or save it as DOCX and upload again.",
        )
        converted = output / f"{path.stem}.docx"
        if not converted.is_file():
            raise ExtractionError("LibreOffice could not convert this DOC file. Save it as DOCX and upload again.")
        return _docx_text(converted)


def extract_sections(path: Path) -> Iterator[tuple[str | None, str]]:
    """Yield a source location and its text, keeping PDF pages and sheets separate."""
    extension = path.suffix.lower()
    if extension == ".pdf":
        yield from _pdf_sections(path)
    elif extension == ".xlsx":
        yield from _xlsx_sections(path)
    elif extension == ".xls":
        yield from _xls_sections(path)
    elif extension == ".docx":
        yield None, _docx_text(path)
    elif extension == ".doc":
        yield None, _doc_text(path)
    elif extension in {".png", ".jpg", ".jpeg"}:
        yield None, _ocr(path)
    else:
        raise ExtractionError(f"Unsupported extension: {extension}")
