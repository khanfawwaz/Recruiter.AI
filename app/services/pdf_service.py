"""
File extraction service – supports PDF and plain-text (.txt) uploads.
"""
import io
from fastapi import HTTPException, UploadFile, status
import pdfplumber

from app.config import settings

ALLOWED_EXTENSIONS = (".pdf", ".txt")


def _check_size(content: bytes, filename: str) -> None:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"'{filename}' exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )


def extract_text_from_pdf(content: bytes, filename: str = "file") -> str:
    """
    Extract text from PDF bytes using pdfplumber.
    Raises HTTP 400 on corrupt / empty PDFs.
    """
    _check_size(content, filename)
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
        text = "\n".join(pages).strip()
        if not text:
            raise HTTPException(
                status_code=400,
                detail=f"No text found in '{filename}'. PDF may be scanned/image-only.",
            )
        return text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse '{filename}': {exc}")


def extract_text_from_txt(content: bytes, filename: str) -> str:
    """Decode a plain-text upload."""
    _check_size(content, filename)
    try:
        return content.decode("utf-8", errors="replace").strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read '{filename}': {exc}")


async def read_upload_file(upload: UploadFile) -> bytes:
    """Validate extension and read bytes from an UploadFile."""
    lower = upload.filename.lower()
    if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"'{upload.filename}' must be a .pdf or .txt file.",
        )
    return await upload.read()


def extract_text(content: bytes, filename: str) -> str:
    """Route to the right extractor based on file extension."""
    if filename.lower().endswith(".txt"):
        return extract_text_from_txt(content, filename)
    return extract_text_from_pdf(content, filename)
