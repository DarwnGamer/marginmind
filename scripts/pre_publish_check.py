from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "storage"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"DEEPSEEK_API_KEY\s*=\s*sk-[A-Za-z0-9_\-]+"),
    re.compile(r"OPENAI_API_KEY\s*=\s*sk-[A-Za-z0-9_\-]+"),
]
LOCAL_ONLY = [
    ".env",
    "storage",
    "server.err.log",
    "server.out.log",
    "想法.txt",
]


def main() -> int:
    problems: list[str] = []
    warnings: list[str] = []

    for item in LOCAL_ONLY:
        path = ROOT / item
        if path.exists():
            warnings.append(f"local-only path exists: {item}")

    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.name == ".env":
            continue
        text = _read_text(path)
        if text is None:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                problems.append(str(path.relative_to(ROOT)))
                break

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
        print()

    if problems:
        print("Potential secrets found:")
        for problem in sorted(set(problems)):
            print(f"- {problem}")
        return 1

    print("Pre-publish check passed: no obvious API keys found in publishable files.")
    print("Reminder: use git so ignored local files stay out of the GitHub repository.")
    return 0


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
