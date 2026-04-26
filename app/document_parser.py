from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_document(path: Path, original_filename: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        pages = _parse_pdf(path)
    elif suffix == ".docx":
        pages = _parse_docx(path)
    elif suffix in {".txt", ".md"}:
        pages = _parse_text(path)
    else:
        raise ValueError("目前 MVP 支持 PDF、DOCX、TXT、MD。")

    if not pages:
        pages = [{"page_number": 1, "text": "未能从文档中提取到可阅读文字。"}]

    return {
        "title": Path(original_filename).stem,
        "filename": original_filename,
        "page_count": len(pages),
        "pages": pages,
    }


def _parse_pdf(path: Path) -> list[dict[str, Any]]:
    import fitz

    pages: list[dict[str, Any]] = []
    with fitz.open(path) as pdf:
        for index, page in enumerate(pdf, start=1):
            text = page.get_text("text") or ""
            pages.append({"page_number": index, "text": _normalize_text(text)})
    return pages


def _parse_docx(path: Path) -> list[dict[str, Any]]:
    from docx import Document

    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return _chunk_text("\n\n".join(paragraphs))


def _parse_text(path: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    return _chunk_text(text)


def _chunk_text(text: str, max_chars: int = 2400) -> list[dict[str, Any]]:
    text = _normalize_text(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    pages: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            pages.append(current)
        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for start in range(0, len(paragraph), max_chars):
                chunk = paragraph[start : start + max_chars]
                if len(chunk) == max_chars:
                    pages.append(chunk)
                else:
                    current = chunk
    if current:
        pages.append(current)

    return [{"page_number": index, "text": page} for index, page in enumerate(pages, start=1)]


def _normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    normalized: list[str] = []
    blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not blank:
                normalized.append("")
            blank = True
            continue
        normalized.append(stripped)
        blank = False
    return "\n".join(normalized).strip()
