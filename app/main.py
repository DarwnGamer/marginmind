from __future__ import annotations

import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .attention import analyze_session
from .document_renderer import ensure_parsed_document, get_page_payload, pdf_page_image, quick_document_metadata
from .note_generator import generate_notes
from .storage import (
    DOCUMENTS_DIR,
    ROOT_DIR,
    SESSIONS_DIR,
    append_jsonl,
    ensure_storage,
    now_iso,
    read_json,
    read_jsonl,
    write_json,
)


ensure_storage()

app = FastAPI(title="MarginMind MVP")
app.mount("/static", StaticFiles(directory=ROOT_DIR / "static"), name="static")

GAZE_PROCESSES: dict[str, subprocess.Popen[Any]] = {}
MIN_PAGE_DWELL_SECONDS = 3.0
MIN_PAGE_GAZE_SECONDS = 1.0


class SessionCreate(BaseModel):
    document_id: str
    note_goal: str = ""
    reader_profile: dict[str, Any] = Field(default_factory=dict)


class EventBatch(BaseModel):
    events: list[dict[str, Any]]


class PageLayout(BaseModel):
    page_number: int
    viewport: dict[str, Any]
    spans: list[dict[str, Any]]
    ts: float | None = None


class GazeStart(BaseModel):
    session_id: str
    camera_id: int = 0
    sample_hz: int = 24
    preview: bool = False
    calibrate: bool = True


class GazeStop(BaseModel):
    session_id: str


class GazeSamples(BaseModel):
    session_id: str
    samples: list[dict[str, Any]]


class NoteRequest(BaseModel):
    note_goal: str | None = None
    use_ai: bool = True


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT_DIR / "static" / "index.html")


@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名。")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="目前 MVP 支持 PDF、DOCX、TXT、MD。")

    doc_id = uuid.uuid4().hex
    doc_dir = DOCUMENTS_DIR / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    source_path = doc_dir / f"source{suffix}"
    source_path.write_bytes(await file.read())

    try:
        document = quick_document_metadata(source_path, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"文档读取失败：{exc}") from exc

    document.update({"id": doc_id, "created_at": now_iso(), "source_path": str(source_path), "pages": []})
    write_json(doc_dir / "document.json", document)
    return _document_public(document)


@app.get("/api/documents/{document_id}")
def get_document(document_id: str) -> dict[str, Any]:
    document = _load_document(document_id)
    return _document_public(document)


@app.get("/api/documents/{document_id}/page/{page_number}")
def get_document_page(document_id: str, page_number: int) -> dict[str, Any]:
    document = _load_document(document_id)
    try:
        return get_page_payload(document, DOCUMENTS_DIR / document_id, page_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/documents/{document_id}/page/{page_number}/image")
def get_document_page_image(document_id: str, page_number: int) -> FileResponse:
    document = _load_document(document_id)
    try:
        return pdf_page_image(document, DOCUMENTS_DIR / document_id, page_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/sessions")
def create_session(payload: SessionCreate) -> dict[str, Any]:
    document = _load_document(payload.document_id)
    session_id = uuid.uuid4().hex
    session_dir = SESSIONS_DIR / session_id
    (session_dir / "layouts").mkdir(parents=True, exist_ok=True)
    session = {
        "id": session_id,
        "document_id": payload.document_id,
        "document_title": document.get("title"),
        "note_goal": payload.note_goal,
        "reader_profile": payload.reader_profile,
        "created_at": now_iso(),
        "gaze": {"status": "idle", "provider": "GazeFollower"},
    }
    write_json(session_dir / "session.json", session)
    return session


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    return _load_session(session_id)


@app.post("/api/sessions/{session_id}/page-layout")
def save_page_layout(session_id: str, payload: PageLayout) -> dict[str, Any]:
    session_dir = _session_dir(session_id)
    layout = payload.model_dump()
    layout["server_ts"] = time.time()
    write_json(session_dir / "layouts" / f"page_{payload.page_number}.json", layout)
    append_jsonl(
        session_dir / "events.jsonl",
        [
            {
                "type": "layout",
                "page_number": payload.page_number,
                "ts": payload.ts or time.time(),
                "server_ts": time.time(),
                "span_count": len(payload.spans),
            }
        ],
    )
    return {"ok": True, "span_count": len(payload.spans)}


@app.post("/api/sessions/{session_id}/events")
def save_events(session_id: str, payload: EventBatch) -> dict[str, Any]:
    session_dir = _session_dir(session_id)
    rows = []
    for event in payload.events:
        if not isinstance(event, dict):
            continue
        event.setdefault("ts", time.time())
        event["server_ts"] = time.time()
        rows.append(event)
    append_jsonl(session_dir / "events.jsonl", rows)
    return {"ok": True, "count": len(rows)}


@app.post("/api/gaze/start")
def start_gaze(request: Request, payload: GazeStart) -> dict[str, Any]:
    session = _load_session(payload.session_id)
    session_dir = _session_dir(payload.session_id)
    existing = GAZE_PROCESSES.get(payload.session_id)
    if existing and existing.poll() is None:
        return {"ok": True, "status": "running", "pid": existing.pid}

    stop_file = session_dir / "stop_gaze.flag"
    if stop_file.exists():
        stop_file.unlink()

    api_url = str(request.base_url).rstrip("/")
    log_path = session_dir / "gaze_worker.log"
    cmd = [
        sys.executable,
        "-m",
        "app.gaze_worker",
        "--session-id",
        payload.session_id,
        "--api-url",
        api_url,
        "--session-dir",
        str(session_dir),
        "--camera-id",
        str(payload.camera_id),
        "--sample-hz",
        str(max(1, min(payload.sample_hz, 60))),
        "--stop-file",
        str(stop_file),
    ]
    if not payload.preview:
        cmd.append("--no-preview")
    if not payload.calibrate:
        cmd.append("--skip-calibration")

    with log_path.open("ab") as log:
        process = subprocess.Popen(cmd, cwd=str(ROOT_DIR), stdout=log, stderr=subprocess.STDOUT)

    GAZE_PROCESSES[payload.session_id] = process
    session["gaze"] = {"status": "starting", "provider": "GazeFollower", "pid": process.pid}
    write_json(session_dir / "session.json", session)
    append_jsonl(
        session_dir / "events.jsonl",
        [{"type": "gaze_worker_start_requested", "ts": time.time(), "pid": process.pid}],
    )
    return {"ok": True, "status": "starting", "pid": process.pid}


@app.post("/api/gaze/stop")
def stop_gaze(payload: GazeStop) -> dict[str, Any]:
    session_dir = _session_dir(payload.session_id)
    (session_dir / "stop_gaze.flag").write_text("stop", encoding="utf-8")
    process = GAZE_PROCESSES.get(payload.session_id)
    stopped = False
    if process and process.poll() is None:
        try:
            process.wait(timeout=3)
            stopped = True
        except subprocess.TimeoutExpired:
            process.terminate()
            stopped = True
    session = _load_session(payload.session_id)
    session["gaze"] = {"status": "stopped", "provider": "GazeFollower"}
    write_json(session_dir / "session.json", session)
    append_jsonl(session_dir / "events.jsonl", [{"type": "gaze_worker_stop_requested", "ts": time.time()}])
    return {"ok": True, "stopped": stopped}


@app.get("/api/gaze/status/{session_id}")
def gaze_status(session_id: str) -> dict[str, Any]:
    session_dir = _session_dir(session_id)
    process = GAZE_PROCESSES.get(session_id)
    status = "not_started"
    pid = None
    return_code = None
    if process:
        pid = process.pid
        return_code = process.poll()
        status = "running" if return_code is None else "exited"
    session = read_json(session_dir / "session.json", default={})
    if session.get("gaze", {}).get("status") in {"starting", "sampling", "error"} and status == "not_started":
        status = session["gaze"]["status"]
    events = read_jsonl(session_dir / "events.jsonl")
    phase, progress = _gaze_phase(events, status)
    return {
        "status": status,
        "phase": phase,
        "progress": progress,
        "pid": pid,
        "return_code": return_code,
        "sample_count": len(read_jsonl(session_dir / "gaze_samples.jsonl")),
        "last_events": events[-5:],
    }


@app.post("/api/gaze/samples")
def ingest_gaze_samples(payload: GazeSamples) -> dict[str, Any]:
    session_dir = _session_dir(payload.session_id)
    rows = []
    for sample in payload.samples:
        sample.setdefault("ts", time.time())
        sample["server_ts"] = time.time()
        rows.append(sample)
    append_jsonl(session_dir / "gaze_samples.jsonl", rows)
    return {"ok": True, "count": len(rows)}


@app.post("/api/sessions/{session_id}/notes")
def create_notes(session_id: str, payload: NoteRequest) -> dict[str, Any]:
    session = _load_session(session_id)
    document_id = session["document_id"]
    document = ensure_parsed_document(_load_document(document_id), DOCUMENTS_DIR / document_id)
    session_dir = _session_dir(session_id)
    note_goal = payload.note_goal if payload.note_goal is not None else session.get("note_goal", "")
    analysis = analyze_session(session_dir, document)
    scoped_document, scoped_analysis, read_pages = _scope_to_read_pages(document, analysis, session_dir)
    generation = generate_notes(
        document=scoped_document,
        analysis=scoped_analysis,
        note_goal=note_goal,
        reader_profile=session.get("reader_profile", {}),
        use_ai=payload.use_ai,
    )
    (session_dir / "notes.md").write_text(generation["notes"], encoding="utf-8")
    (session_dir / "ai_prompt.md").write_text(generation["ai_prompt"], encoding="utf-8")
    write_json(session_dir / "ai_context.json", generation["ai_context"])
    write_json(session_dir / "read_scope.json", {"read_pages": read_pages})
    session["note_goal"] = note_goal
    session["notes_provider"] = generation["provider"]
    session["notes_generated_at"] = now_iso()
    session["read_pages"] = read_pages
    write_json(session_dir / "session.json", session)
    return {
        "notes": generation["notes"],
        "provider": generation["provider"],
        "analysis": scoped_analysis,
        "read_pages": read_pages,
    }


def _document_public(document: dict[str, Any]) -> dict[str, Any]:
    public = dict(document)
    public.pop("source_path", None)
    public.pop("pages", None)
    return public


def _load_document(document_id: str) -> dict[str, Any]:
    path = DOCUMENTS_DIR / document_id / "document.json"
    document = read_json(path)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在。")
    return document


def _load_session(session_id: str) -> dict[str, Any]:
    session = read_json(_session_dir(session_id) / "session.json")
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在。")
    return session


def _session_dir(session_id: str) -> Path:
    path = SESSIONS_DIR / session_id
    if not path.exists():
        raise HTTPException(status_code=404, detail="会话不存在。")
    return path


def _gaze_phase(events: list[dict[str, Any]], status: str) -> tuple[str, int]:
    phase_map = [
        ("gaze_worker_start_requested", "启动进程", 8),
        ("gaze_worker_boot", "进程已启动", 14),
        ("gaze_import_start", "导入视线追踪库", 22),
        ("gaze_import_end", "视线追踪库已导入", 34),
        ("gaze_display_start", "准备校准窗口", 42),
        ("gaze_instance_start", "加载模型与摄像头", 50),
        ("gaze_instance_end", "模型已就绪", 58),
        ("gaze_worker_ready", "摄像头就绪", 64),
        ("gaze_preview_start", "预览摄像头", 66),
        ("gaze_preview_end", "预览完成", 70),
        ("gaze_calibration_start", "正在校准", 72),
        ("gaze_calibration_end", "校准完成", 88),
        ("gaze_sampling_start", "正在采样", 100),
        ("gaze_worker_error", "出错", 100),
    ]
    seen = {event.get("type") for event in events}
    phase = "未启动"
    progress = 0
    for event_type, label, value in phase_map:
        if event_type in seen:
            phase = label
            progress = value
    if status == "running" and progress < 8:
        phase = "启动中"
        progress = 8
    return phase, progress


def _scope_to_read_pages(
    document: dict[str, Any],
    analysis: dict[str, Any],
    session_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any], list[int]]:
    events = read_jsonl(session_dir / "events.jsonl")
    page_dwell = _page_dwell_seconds(events, end_ts=time.time())
    read_pages: set[int] = set()
    has_reading_activity = any(
        event.get("type") in {"page_view", "page_change", "layout", "layout_change", "text_selection"}
        for event in events
    )

    for event in events:
        if event.get("type") != "text_selection":
            continue
        page_number = event.get("page_number")
        if page_number:
            read_pages.add(int(page_number))

    for page in analysis.get("pages", []):
        page_number = page.get("page_number")
        if not page_number:
            continue
        if page.get("total_gaze_seconds", 0) >= MIN_PAGE_GAZE_SECONDS or page.get("selections"):
            read_pages.add(int(page_number))

    for page_number, dwell_seconds in page_dwell.items():
        if dwell_seconds >= MIN_PAGE_DWELL_SECONDS:
            read_pages.add(page_number)

    all_pages = document.get("pages", [])
    if not read_pages and not has_reading_activity:
        read_pages = {int(page.get("page_number")) for page in all_pages if page.get("page_number")}

    sorted_pages = sorted(read_pages)
    scoped_document = dict(document)
    scoped_document["pages"] = [page for page in all_pages if int(page.get("page_number", 0)) in read_pages]
    scoped_document["page_count"] = len(scoped_document["pages"])

    scoped_analysis = dict(analysis)
    scoped_analysis["pages"] = [
        page for page in analysis.get("pages", []) if int(page.get("page_number", 0)) in read_pages
    ]
    scoped_analysis["page_count"] = len(scoped_analysis["pages"])
    scoped_analysis["read_scope"] = {
        "read_pages": sorted_pages,
        "page_dwell_seconds": {str(key): round(value, 2) for key, value in sorted(page_dwell.items())},
        "min_page_dwell_seconds": MIN_PAGE_DWELL_SECONDS,
        "min_page_gaze_seconds": MIN_PAGE_GAZE_SECONDS,
    }

    return scoped_document, scoped_analysis, sorted_pages


def _page_dwell_seconds(events: list[dict[str, Any]], end_ts: float) -> dict[int, float]:
    page_views: list[tuple[float, int]] = []
    for event in events:
        if event.get("type") not in {"page_view", "page_change"}:
            continue
        page_number = event.get("page_number")
        ts = event.get("ts") or event.get("timestamp") or event.get("server_ts")
        if page_number and ts:
            page_views.append((float(ts), int(page_number)))

    page_views.sort(key=lambda item: item[0])
    dwell: dict[int, float] = {}
    for index, (ts, page_number) in enumerate(page_views):
        next_ts = page_views[index + 1][0] if index + 1 < len(page_views) else end_ts
        delta = max(0.0, min(next_ts - ts, 60.0))
        dwell[page_number] = dwell.get(page_number, 0.0) + delta
    return dwell
