from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)
    content = ("第一页内容。" * 260 + "\n\n" + "第二页内容。" * 260).encode("utf-8")
    upload = client.post(
        "/api/documents",
        files={"file": ("scope.txt", io.BytesIO(content), "text/plain")},
    )
    upload.raise_for_status()
    document = upload.json()

    session_resp = client.post(
        "/api/sessions",
        json={"document_id": document["id"], "note_goal": "只总结已读页", "reader_profile": {}},
    )
    session_resp.raise_for_status()
    session = session_resp.json()

    layout = {
        "page_number": 1,
        "viewport": {"inner_width": 1200, "inner_height": 800},
        "spans": [
            {
                "id": "1-0",
                "text": "第一页内容。",
                "boxes": [{"x": 100, "y": 100, "w": 220, "h": 40}],
            }
        ],
        "ts": 1000.0,
    }
    client.post(f"/api/sessions/{session['id']}/page-layout", json=layout).raise_for_status()
    client.post(
        f"/api/sessions/{session['id']}/events",
        json={"events": [{"type": "page_view", "page_number": 1, "ts": 1000.0}]},
    ).raise_for_status()
    client.post(
        "/api/gaze/samples",
        json={"session_id": session["id"], "samples": [{"ts": 1000.1, "x": 120, "y": 120, "valid": True}]},
    ).raise_for_status()

    notes = client.post(f"/api/sessions/{session['id']}/notes", json={"use_ai": False})
    notes.raise_for_status()
    payload = notes.json()
    assert payload["read_pages"] == [1], payload["read_pages"]
    print("read scope ok")


def continuous_flip_case() -> None:
    client = TestClient(app)
    content = ("第一页内容。" * 260 + "\n\n" + "第二页内容。" * 260 + "\n\n" + "第三页内容。" * 260).encode("utf-8")
    upload = client.post(
        "/api/documents",
        files={"file": ("flip.txt", io.BytesIO(content), "text/plain")},
    )
    upload.raise_for_status()
    document = upload.json()
    session_resp = client.post(
        "/api/sessions",
        json={"document_id": document["id"], "note_goal": "只总结稳定阅读页", "reader_profile": {}},
    )
    session_resp.raise_for_status()
    session = session_resp.json()

    base_ts = time.time()
    for index, page_number in enumerate([1, 2, 3]):
        ts = base_ts + index * 0.35
        client.post(
            f"/api/sessions/{session['id']}/events",
            json={"events": [{"type": "layout_change", "reason": "page_change", "page_number": page_number, "ts": ts}]},
        ).raise_for_status()
        client.post(
            f"/api/sessions/{session['id']}/events",
            json={"events": [{"type": "page_view", "page_number": page_number, "ts": ts + 0.02}]},
        ).raise_for_status()
        layout = {
            "page_number": page_number,
            "viewport": {"inner_width": 1200, "inner_height": 800},
            "spans": [
                {
                    "id": f"{page_number}-0",
                    "text": f"第{page_number}页内容。",
                    "boxes": [{"x": 100, "y": 100, "w": 220, "h": 40}],
                }
            ],
            "ts": ts + 0.03,
        }
        client.post(f"/api/sessions/{session['id']}/page-layout", json=layout).raise_for_status()

    notes = client.post(f"/api/sessions/{session['id']}/notes", json={"use_ai": False})
    notes.raise_for_status()
    payload = notes.json()
    assert payload["read_pages"] == [], payload["read_pages"]
    print("continuous flip scope ok")


if __name__ == "__main__":
    main()
    continuous_flip_case()
