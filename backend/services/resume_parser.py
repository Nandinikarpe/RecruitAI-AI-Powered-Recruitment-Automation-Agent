import io
import re
import PyPDF2
import docx
from typing import Optional


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    raise ValueError(f"Unsupported file type: {ext}")


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str:
    """Heuristic: first non-empty line is usually the candidate name."""
    for line in text.splitlines():
        line = line.strip()
        if line and len(line.split()) >= 2 and len(line) < 60:
            return line
    return "Unknown"
