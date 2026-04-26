from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)
    content = (
        "澜页是一款阅读学习笔记工具。\n\n"
        "它使用摄像头视线追踪来判断用户真正关注的内容，并生成带依据的笔记。"
    ).encode("utf-8")

    upload = client.post(
        "/api/documents",
        files={"file": ("sample.txt", io.BytesIO(content), "text/plain")},
    )
    upload.raise_for_status()
    document = upload.json()

    session_resp = client.post(
        "/api/sessions",
        json={
            "document_id": document["id"],
            "note_goal": "生成复习笔记，并指出可能忽略的内容",
            "reader_profile": {"purpose": "复习巩固"},
        },
    )
    session_resp.raise_for_status()
    session = session_resp.json()

    page_layout = {
        "page_number": 1,
        "viewport": {"inner_width": 1200, "inner_height": 800},
        "spans": [
            {
                "id": "1-0",
                "text": "澜页是一款阅读学习笔记工具。",
                "boxes": [{"x": 100, "y": 100, "w": 420, "h": 40}],
            },
            {
                "id": "1-1",
                "text": "它使用摄像头视线追踪来判断用户真正关注的内容",
                "boxes": [{"x": 100, "y": 160, "w": 620, "h": 40}],
            },
        ],
        "ts": 1000.0,
    }
    client.post(f"/api/sessions/{session['id']}/page-layout", json=page_layout).raise_for_status()
    client.post(
        f"/api/sessions/{session['id']}/events",
        json={"events": [{"type": "page_view", "page_number": 1, "ts": 1000.0}]},
    ).raise_for_status()
    client.post(
        "/api/gaze/samples",
        json={
            "session_id": session["id"],
            "samples": [
                {"ts": 1000.01, "x": 140, "y": 115, "valid": True},
                {"ts": 1000.16, "x": 160, "y": 118, "valid": True},
                {"ts": 1000.31, "x": 180, "y": 170, "valid": True},
                {"ts": 1000.46, "x": 200, "y": 170, "valid": True},
            ],
        },
    ).raise_for_status()

    notes = client.post(f"/api/sessions/{session['id']}/notes", json={"use_ai": False})
    notes.raise_for_status()
    payload = notes.json()
    assert payload["provider"] == "local"
    assert payload["analysis"]["sample_count"] == 4
    assert payload["analysis"]["pages"][0]["top_focus"]
    print("smoke ok")


if __name__ == "__main__":
    main()
