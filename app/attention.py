from __future__ import annotations

from bisect import bisect_right
from pathlib import Path
from typing import Any

from .storage import read_json, read_jsonl, write_json


def analyze_session(session_dir: Path, document: dict[str, Any]) -> dict[str, Any]:
    events = read_jsonl(session_dir / "events.jsonl")
    samples = read_jsonl(session_dir / "gaze_samples.jsonl")
    layouts = _load_layouts(session_dir / "layouts")
    page_views = _page_view_timeline(events)
    layout_changes = _event_times(events, "layout_change")
    selections = _selection_events(events)

    page_results = {
        int(page["page_number"]): {
            "page_number": int(page["page_number"]),
            "total_gaze_seconds": 0.0,
            "segment_seconds": {},
            "top_focus": [],
            "skimmed": [],
            "selections": [],
        }
        for page in document.get("pages", [])
    }

    if page_views and layouts and samples:
        _merge_gaze_with_layout(page_results, page_views, layouts, samples, layout_changes)

    analysis = _finalize(
        page_results=page_results,
        selections=selections,
        document=document,
        layouts_by_page=layouts,
        sample_count=len(samples),
        layout_count=len(layouts),
    )
    write_json(session_dir / "analysis.json", analysis)
    return analysis


def _merge_gaze_with_layout(
    page_results: dict[int, dict[str, Any]],
    page_views: list[tuple[float, int]],
    layouts: dict[int, dict[str, Any]],
    samples: list[dict[str, Any]],
    layout_changes: list[float],
) -> None:
    page_times = [item[0] for item in page_views]
    ordered_samples = sorted(samples, key=lambda item: float(item.get("ts") or item.get("timestamp") or 0))
    for index, sample in enumerate(ordered_samples):
        if not _valid_sample(sample):
            continue
        ts = float(sample.get("ts") or sample.get("timestamp") or 0)
        if _near_layout_change(ts, layout_changes):
            continue
        timeline_index = bisect_right(page_times, ts) - 1
        if timeline_index < 0:
            continue
        page_number = int(page_views[timeline_index][1])
        layout = layouts.get(page_number)
        if not layout:
            continue

        viewport_point = _sample_to_viewport(sample, layout.get("viewport", {}))
        if viewport_point is None:
            continue
        x, y = viewport_point
        dt = _sample_duration(ordered_samples, index)

        page_results.setdefault(
            page_number,
            {
                "page_number": page_number,
                "total_gaze_seconds": 0.0,
                "segment_seconds": {},
                "top_focus": [],
                "skimmed": [],
                "selections": [],
            },
        )
        page_results[page_number]["total_gaze_seconds"] += dt

        for span in layout.get("spans", []):
            if _point_hits_span(x, y, span):
                segment_id = str(span.get("id"))
                seconds = page_results[page_number]["segment_seconds"].get(segment_id, 0.0)
                page_results[page_number]["segment_seconds"][segment_id] = seconds + dt
                break


def _load_layouts(layout_dir: Path) -> dict[int, dict[str, Any]]:
    layouts: dict[int, dict[str, Any]] = {}
    if not layout_dir.exists():
        return layouts
    for path in layout_dir.glob("page_*.json"):
        layout = read_json(path, default={})
        page_number = int(layout.get("page_number") or 0)
        if page_number:
            layouts[page_number] = layout
    return layouts


def _page_view_timeline(events: list[dict[str, Any]]) -> list[tuple[float, int]]:
    timeline: list[tuple[float, int]] = []
    for event in events:
        if event.get("type") not in {"page_view", "page_change"}:
            continue
        page_number = event.get("page_number")
        ts = event.get("ts") or event.get("timestamp") or event.get("server_ts")
        if not page_number or not ts:
            continue
        timeline.append((float(ts), int(page_number)))
    timeline.sort(key=lambda item: item[0])
    return timeline


def _event_times(events: list[dict[str, Any]], event_type: str) -> list[float]:
    times = []
    for event in events:
        if event.get("type") != event_type:
            continue
        ts = event.get("ts") or event.get("timestamp") or event.get("server_ts")
        if ts:
            times.append(float(ts))
    return sorted(times)


def _near_layout_change(ts: float, layout_changes: list[float], window_seconds: float = 0.8) -> bool:
    if not layout_changes:
        return False
    index = bisect_right(layout_changes, ts)
    neighbors = []
    if index > 0:
        neighbors.append(layout_changes[index - 1])
    if index < len(layout_changes):
        neighbors.append(layout_changes[index])
    return any(abs(ts - item) <= window_seconds for item in neighbors)


def _selection_events(events: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    selections: dict[int, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("type") != "text_selection":
            continue
        text = str(event.get("text") or "").strip()
        page_number = int(event.get("page_number") or 0)
        if not text or not page_number:
            continue
        selections.setdefault(page_number, []).append(
            {
                "text": _trim(text, 500),
                "ts": event.get("ts") or event.get("timestamp") or event.get("server_ts"),
            }
        )
    return selections


def _valid_sample(sample: dict[str, Any]) -> bool:
    if sample.get("valid") is False:
        return False
    x = sample.get("x")
    y = sample.get("y")
    if x is None or y is None:
        return False
    try:
        return float(x) > -1000 and float(y) > -1000
    except (TypeError, ValueError):
        return False


def _sample_duration(samples: list[dict[str, Any]], index: int) -> float:
    current_ts = float(samples[index].get("ts") or samples[index].get("timestamp") or 0)
    if index + 1 < len(samples):
        next_ts = float(samples[index + 1].get("ts") or samples[index + 1].get("timestamp") or current_ts)
        delta = next_ts - current_ts
        if 0 < delta <= 0.5:
            return delta
    return 1 / 24


def _sample_to_viewport(sample: dict[str, Any], viewport: dict[str, Any]) -> tuple[float, float] | None:
    try:
        x = float(sample.get("x"))
        y = float(sample.get("y"))
    except (TypeError, ValueError):
        return None

    inner_width = float(viewport.get("inner_width") or viewport.get("width") or 0)
    inner_height = float(viewport.get("inner_height") or viewport.get("height") or 0)
    if inner_width and inner_height and 0 <= x <= inner_width and 0 <= y <= inner_height:
        return x, y

    screen_left = float(viewport.get("screen_left") or 0)
    screen_top = float(viewport.get("screen_top") or 0)
    chrome_y = max(0.0, float(viewport.get("outer_height") or 0) - inner_height)
    vx = x - screen_left
    vy = y - screen_top - chrome_y
    if inner_width and inner_height and -80 <= vx <= inner_width + 80 and -80 <= vy <= inner_height + 80:
        return vx, vy
    return x, y


def _point_hits_span(x: float, y: float, span: dict[str, Any], padding: float = 10) -> bool:
    for box in span.get("boxes", []):
        bx = float(box.get("x") or 0)
        by = float(box.get("y") or 0)
        bw = float(box.get("w") or 0)
        bh = float(box.get("h") or 0)
        if bx - padding <= x <= bx + bw + padding and by - padding <= y <= by + bh + padding:
            return True
    return False


def _finalize(
    page_results: dict[int, dict[str, Any]],
    selections: dict[int, list[dict[str, Any]]],
    document: dict[str, Any],
    layouts_by_page: dict[int, dict[str, Any]],
    sample_count: int,
    layout_count: int,
) -> dict[str, Any]:
    for page_number, result in page_results.items():
        result["selections"] = selections.get(page_number, [])
        result["segment_seconds"] = {
            str(segment_id): round(float(seconds), 3)
            for segment_id, seconds in result.get("segment_seconds", {}).items()
        }

    for page_number, result in page_results.items():
        layout = layouts_by_page.get(page_number, {})
        spans_by_id = {str(span.get("id")): span for span in layout.get("spans", [])}
        ranked = sorted(result.get("segment_seconds", {}).items(), key=lambda item: item[1], reverse=True)

        top_focus = []
        for segment_id, seconds in ranked[:8]:
            if seconds < 0.18:
                continue
            text = _trim(str(spans_by_id.get(segment_id, {}).get("text") or ""), 220)
            if text:
                top_focus.append({"text": text, "seconds": seconds})
        result["top_focus"] = top_focus

        read_ids = {segment_id for segment_id, seconds in ranked if seconds >= 0.12}
        skimmed = []
        for span in layout.get("spans", []):
            segment_id = str(span.get("id"))
            text = _trim(str(span.get("text") or ""), 180)
            if len(text) >= 12 and segment_id not in read_ids:
                skimmed.append({"text": text, "seconds": result.get("segment_seconds", {}).get(segment_id, 0.0)})
            if len(skimmed) >= 6:
                break
        result["skimmed"] = skimmed
        result["total_gaze_seconds"] = round(float(result.get("total_gaze_seconds", 0.0)), 2)

    return {
        "sample_count": sample_count,
        "layout_count": layout_count,
        "page_count": len(document.get("pages", [])),
        "pages": [page_results[key] for key in sorted(page_results)],
    }


def _trim(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
