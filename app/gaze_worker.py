from __future__ import annotations

import argparse
import math
import time
from pathlib import Path
from typing import Any

import requests


def main() -> int:
    parser = argparse.ArgumentParser(description="MarginMind GazeFollower sampling worker")
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--camera-id", type=int, default=0)
    parser.add_argument("--sample-hz", type=int, default=24)
    parser.add_argument("--stop-file", required=True)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--skip-calibration", action="store_true")
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    stop_file = Path(args.stop_file)
    api_url = args.api_url.rstrip("/")
    sample_interval = 1 / max(1, min(args.sample_hz, 60))

    def event(event_type: str, **data: Any) -> None:
        _post_event(api_url, args.session_id, {"type": event_type, "ts": time.time(), **data})

    event("gaze_worker_boot", provider="GazeFollower")

    try:
        event("gaze_import_start")
        import pygame
        from gazefollower import GazeFollower
        from gazefollower.camera import WebCamCamera
        event("gaze_import_end")
    except Exception as exc:
        event("gaze_worker_error", message=f"GazeFollower 导入失败：{exc}")
        return 2

    event("gaze_display_start")
    pygame.init()
    pygame.display.init()
    info = pygame.display.Info()
    width = info.current_w or 1280
    height = info.current_h or 720
    win = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
    pygame.display.set_caption("MarginMind Gaze Calibration")
    _raise_pygame_window(pygame)

    gaze_follower = None
    try:
        event("gaze_instance_start")
        gaze_follower = GazeFollower(camera=WebCamCamera(webcam_id=args.camera_id))
        event("gaze_instance_end")
        event("gaze_worker_ready", screen_width=width, screen_height=height, camera_id=args.camera_id)

        if not args.no_preview:
            event("gaze_preview_start")
            _raise_pygame_window(pygame)
            gaze_follower.preview(win=win)
            event("gaze_preview_end")

        if not args.skip_calibration:
            event("gaze_calibration_start")
            _raise_pygame_window(pygame)
            gaze_follower.calibrate(win=win)
            event("gaze_calibration_end")

        gaze_follower.start_sampling()
        event("gaze_sampling_start", sample_hz=args.sample_hz)
        try:
            pygame.display.iconify()
        except Exception:
            pass

        batch: list[dict[str, Any]] = []
        last_post = time.time()
        sample_index = 0
        while not stop_file.exists():
            for pygame_event in pygame.event.get():
                if pygame_event.type == pygame.QUIT:
                    stop_file.write_text("quit", encoding="utf-8")

            gaze_info = gaze_follower.get_gaze_info()
            sample = _sample_from_gaze_info(gaze_info, sample_index)
            batch.append(sample)
            sample_index += 1

            if len(batch) >= 12 or time.time() - last_post >= 0.75:
                _post_samples(api_url, args.session_id, batch)
                batch = []
                last_post = time.time()
            time.sleep(sample_interval)

        if batch:
            _post_samples(api_url, args.session_id, batch)
        event("gaze_sampling_stop", samples=sample_index)
        return 0
    except Exception as exc:
        event("gaze_worker_error", message=str(exc))
        return 1
    finally:
        try:
            if gaze_follower is not None:
                gaze_follower.stop_sampling()
                raw_path = session_dir / "gazefollower_raw.csv"
                gaze_follower.save_data(str(raw_path))
                gaze_follower.release()
        except Exception as exc:
            event("gaze_worker_release_error", message=str(exc))
        try:
            pygame.quit()
        except Exception:
            pass


def _sample_from_gaze_info(gaze_info: Any, sample_index: int) -> dict[str, Any]:
    filtered = _get_attr(gaze_info, "filtered_gaze_coordinates")
    calibrated = _get_attr(gaze_info, "calibrated_gaze_coordinates")
    raw = _first_present(_get_attr(gaze_info, "raw_gaze_coordinates"), _get_attr(gaze_info, "gaze_coordinates"))
    status = _get_attr(gaze_info, "status")
    event = _get_attr(gaze_info, "event")
    tracking_state = _get_attr(gaze_info, "tracking_state")

    x, y = _xy(_first_present(filtered, calibrated, raw))
    raw_x, raw_y = _xy(raw)
    valid = x is not None and y is not None and _finite(x) and _finite(y) and x > -1000 and y > -1000
    if status is not None and str(status).lower() in {"invalid", "false", "0"}:
        valid = False

    return {
        "source": "GazeFollower",
        "index": sample_index,
        "ts": time.time(),
        "monotonic": time.perf_counter(),
        "x": x,
        "y": y,
        "raw_x": raw_x,
        "raw_y": raw_y,
        "valid": valid,
        "status": str(status) if status is not None else None,
        "event": str(event) if event is not None else None,
        "tracking_state": str(tracking_state) if tracking_state is not None else None,
    }


def _get_attr(obj: Any, name: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _xy(value: Any) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    try:
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None, None
    return None, None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _finite(value: float) -> bool:
    return not math.isnan(value) and not math.isinf(value)


def _post_samples(api_url: str, session_id: str, samples: list[dict[str, Any]]) -> None:
    if not samples:
        return
    try:
        requests.post(
            f"{api_url}/api/gaze/samples",
            json={"session_id": session_id, "samples": samples},
            timeout=2,
        )
    except requests.RequestException:
        pass


def _post_event(api_url: str, session_id: str, event: dict[str, Any]) -> None:
    try:
        requests.post(
            f"{api_url}/api/sessions/{session_id}/events",
            json={"events": [event]},
            timeout=2,
        )
    except requests.RequestException:
        pass


def _raise_pygame_window(pygame_module: Any) -> None:
    try:
        info = pygame_module.display.get_wm_info()
        hwnd = info.get("window")
        if not hwnd:
            return
        import ctypes

        user32 = ctypes.windll.user32
        SW_SHOW = 5
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
