from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.responses import FileResponse

from .document_parser import parse_document
from .storage import write_json


PDF_ZOOM = 2.0
TEXT_PAGE_CHARS = 2200


def quick_document_metadata(path: Path, original_filename: str) -> dict[str, Any]:
    suffix = path.suffix.lower()
    page_count: int | None = None
    render_mode = "text"
    parse_status = "pending"

    if suffix == ".pdf":
        import fitz

        with fitz.open(path) as pdf:
            page_count = pdf.page_count
        render_mode = "pdf-image"
    elif suffix in {".txt", ".md"}:
        page_count = len(_text_pages(path))
    elif suffix == ".docx":
        page_count = 1

    return {
        "title": Path(original_filename).stem,
        "filename": original_filename,
        "suffix": suffix,
        "page_count": page_count or 1,
        "render_mode": render_mode,
        "parse_status": parse_status,
    }


def ensure_parsed_document(document: dict[str, Any], doc_dir: Path) -> dict[str, Any]:
    if document.get("parse_status") == "ready" and document.get("pages"):
        return document
    source_path = Path(document["source_path"])
    parsed = parse_document(source_path, document.get("filename") or source_path.name)
    document["pages"] = parsed.get("pages", [])
    document["page_count"] = parsed.get("page_count") or document.get("page_count") or len(document["pages"])
    document["parse_status"] = "ready"
    write_json(doc_dir / "document.json", document)
    return document


def get_page_payload(document: dict[str, Any], doc_dir: Path, page_number: int) -> dict[str, Any]:
    if page_number < 1 or page_number > int(document.get("page_count") or 1):
        raise ValueError("页码超出范围。")

    if document.get("suffix") == ".pdf":
        return _pdf_page_payload(document, doc_dir, page_number)
    return _text_page_payload(document, doc_dir, page_number)


def pdf_page_image(document: dict[str, Any], doc_dir: Path, page_number: int) -> FileResponse:
    if document.get("suffix") != ".pdf":
        raise ValueError("当前文档不是 PDF。")
    image_path = _render_pdf_page_image(Path(document["source_path"]), doc_dir, page_number)
    return FileResponse(image_path, media_type="image/png")


def _pdf_page_payload(document: dict[str, Any], doc_dir: Path, page_number: int) -> dict[str, Any]:
    import fitz

    source_path = Path(document["source_path"])
    with fitz.open(source_path) as pdf:
        page = pdf[page_number - 1]
        words = page.get_text("words")
        rect = _pdf_content_rect(page.rect, words)
        spans = _pdf_line_spans(words, rect)
    image_path = _render_pdf_page_image(source_path, doc_dir, page_number, rect)

    return {
        "page_number": page_number,
        "page_count": int(document.get("page_count") or 1),
        "render_mode": "pdf-image",
        "image_url": f"/api/documents/{document['id']}/page/{page_number}/image?v={image_path.stat().st_mtime_ns}",
        "source_width": float(rect.width),
        "source_height": float(rect.height),
        "spans": spans,
    }


def _render_pdf_page_image(source_path: Path, doc_dir: Path, page_number: int, crop_rect: Any | None = None) -> Path:
    import fitz

    page_dir = doc_dir / "rendered"
    page_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(source_path) as pdf:
        page = pdf[page_number - 1]
        rect = crop_rect or _pdf_content_rect(page.rect, page.get_text("words"))
        image_path = page_dir / f"page_{page_number}_{int(rect.x0)}_{int(rect.y0)}_{int(rect.x1)}_{int(rect.y1)}.png"
        if image_path.exists():
            return image_path
        pix = page.get_pixmap(matrix=fitz.Matrix(PDF_ZOOM, PDF_ZOOM), clip=rect, alpha=False)
        pix.save(image_path)
    return image_path


def _pdf_content_rect(page_rect: Any, words: list[tuple[Any, ...]]) -> Any:
    import fitz

    if not words:
        return page_rect
    x0 = min(float(word[0]) for word in words)
    y0 = min(float(word[1]) for word in words)
    x1 = max(float(word[2]) for word in words)
    y1 = max(float(word[3]) for word in words)
    padding = 12
    return fitz.Rect(
        max(page_rect.x0, x0 - padding),
        max(page_rect.y0, y0 - padding),
        min(page_rect.x1, x1 + padding),
        min(page_rect.y1, y1 + padding),
    )


def _pdf_line_spans(words: list[tuple[Any, ...]], crop_rect: Any) -> list[dict[str, Any]]:
    lines: dict[tuple[int, int], list[tuple[Any, ...]]] = {}
    for word in words:
        if len(word) < 8:
            continue
        key = (int(word[5]), int(word[6]))
        lines.setdefault(key, []).append(word)

    spans = []
    for index, (_key, line_words) in enumerate(sorted(lines.items(), key=lambda item: (item[1][0][1], item[1][0][0]))):
        line_words.sort(key=lambda item: item[0])
        text = " ".join(str(word[4]) for word in line_words).strip()
        if not text:
            continue
        x0 = min(float(word[0]) for word in line_words)
        y0 = min(float(word[1]) for word in line_words)
        x1 = max(float(word[2]) for word in line_words)
        y1 = max(float(word[3]) for word in line_words)
        spans.append(
            {
                "id": f"line-{index}",
                "text": text,
                "source_box": {
                    "x": x0 - float(crop_rect.x0),
                    "y": y0 - float(crop_rect.y0),
                    "w": x1 - x0,
                    "h": y1 - y0,
                },
            }
        )
    return spans


def _text_page_payload(document: dict[str, Any], doc_dir: Path, page_number: int) -> dict[str, Any]:
    document = ensure_parsed_document(document, doc_dir)
    pages = document.get("pages", [])
    page = pages[page_number - 1] if page_number <= len(pages) else {"text": ""}
    text = str(page.get("text") or "")
    spans = []
    for index, line in enumerate([item.strip() for item in text.splitlines() if item.strip()]):
        spans.append({"id": f"line-{index}", "text": line, "source_box": None})
    return {
        "page_number": page_number,
        "page_count": len(pages) or 1,
        "render_mode": "text",
        "text": text,
        "source_width": 800,
        "source_height": 1100,
        "spans": spans,
    }


def _text_pages(path: Path) -> list[str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    text = text.strip()
    return [text[index : index + TEXT_PAGE_CHARS] for index in range(0, len(text), TEXT_PAGE_CHARS)] or [""]
