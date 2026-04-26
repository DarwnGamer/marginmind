# MarginMind / 澜页

> Statement: the following content was generated with Codex.

[中文](README.md)

<p align="center">
  <img src="static/icon.svg" width="96" height="96" alt="MarginMind icon">
</p>

MarginMind is a local MVP for study-oriented reading. A user uploads a document, reads it in a fixed paged reader, and the app uses webcam-based gaze tracking to estimate which page regions were actually attended to. Notes are generated from the read pages, gaze evidence, explicit text selections, and the user's note request.

> This project is currently a non-commercial prototype. Data is stored locally by default. It does not record audio or upload camera frames; public contributions should use sample configuration and sanitized material.

## Why This Name

The Chinese name “澜页” suggests attention rippling across a page. It is not just an eye-coordinate logger; it tries to turn pauses, skims, and rereads into reviewable reading traces. `MarginMind` combines `Margin` (page margin, annotation space, reading traces) and `Mind` (attention and thinking), leaving room for future reader profiling, review suggestions, attention nudges, and non-traditional note formats.

## Motivation

The original idea was a note-taking tool for learning: while reading, the webcam tracks gaze so the AI can understand where attention went and generate notes that reflect the actual reading process.

The product should not make users passive. AI should provide suggestions, identify blind spots, and support reflection instead of replacing the user's thinking.

## Community

MarginMind is an early MVP. Contributors interested in gaze tracking, document parsing, frontend/backend engineering, privacy and security, usability design, documentation, and open-source governance are welcome. Issues, docs, tests, reproducible bug reports, and small PRs are good starting points.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution notes and [docs/ROADMAP.en.md](docs/ROADMAP.en.md) for planned work.

## Current Features

- Upload `.pdf`, `.docx`, `.txt`, and `.md` files.
- Fast upload path: save file and metadata first; defer heavier parsing.
- Fixed paged reader with no scrolling, so gaze coordinates do not drift across scroll positions.
- PDF pages are rendered from the original PDF; text boxes are extracted from the same page for gaze matching.
- PDF whitespace is cropped to enlarge the readable content; after zooming, the frontend resubmits real screen-space text boxes.
- Local gaze tracking via `GazeFollower`.
- When notes are generated, gaze tracking is stopped and the camera is released.
- Page changes and zoom changes are treated as layout changes; nearby transient gaze samples are filtered to reduce latency errors.
- Rapid continuous flipping does not count as reading. A page must remain stable, accumulate valid gaze, or contain an explicit selection to enter the AI submission scope.
- Only pages actually read in the session are submitted to AI.
- AI input separates original text context from gaze evidence. Final notes must prioritize gaze focus and explicit selections.
- AI providers can be configured through environment variables; local rules are used when no API key is configured.

## Project Structure

```text
marginmind/
├─ app/                    # FastAPI backend, parsing, gaze analysis, note generation
│  ├─ main.py              # API entry point and session workflow
│  ├─ gaze_worker.py       # Local GazeFollower sampling process
│  ├─ attention.py         # Gaze-to-text-box analysis
│  ├─ document_parser.py   # PDF/DOCX/TXT/MD text extraction
│  ├─ document_renderer.py # PDF rendering, whitespace cropping, text box extraction
│  ├─ note_generator.py    # AI provider/local note generation
│  └─ storage.py           # Local storage helpers
├─ static/                 # Frontend upload page, paged reader, result page, icon
├─ tests/                  # Smoke and read-scope tests
├─ docs/                   # Public documentation, roadmap, privacy notes
├─ .github/                # Issue and PR templates
├─ environment.yml         # Conda environment
├─ requirements.txt        # Pip dependencies
├─ .env.example            # Env template with no secrets
└─ README.md               # Chinese README
```

Runtime files are intentionally ignored:

- `storage/`: uploaded files, sessions, gaze samples, internal AI context.
- `server*.log`: local server logs.
- `.env`: local API keys.

These are local runtime files, not repository contents.

## Installation

```powershell
conda env create -f environment.yml
conda activate marginmind
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## API Keys

Copy `.env.example` to `.env` and fill in your own key:

```powershell
Copy-Item .env.example .env
```

Example:

```text
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

OpenAI is optional:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=
```

`.env` is ignored by default; keep real keys local.

## Usage

1. Upload a document.
2. Describe what kind of notes you need.
3. Start gaze tracking and finish GazeFollower calibration.
4. Return to the browser and read in the fixed paged reader.
5. Optionally select text as explicit attention markers.
6. Generate notes. The app stops gaze tracking before note generation.
7. The result page shows the pages submitted to AI, so the output can be checked against the actual read scope.

## Privacy And Safety

- No audio recording.
- No camera frame upload.
- Gaze samples, uploaded documents, AI prompts, and internal context are stored locally in `storage/`.
- Hardware camera indicator lights usually cannot be disabled independently by generic app code; stopping gaze tracking releases the camera.
- Use sanitized material in public issues, pull requests, and screenshots.

See [docs/PRIVACY.en.md](docs/PRIVACY.en.md).

Maintainers can use [docs/PUBLISH_CHECKLIST.en.md](docs/PUBLISH_CHECKLIST.en.md) and run:

```powershell
python scripts\pre_publish_check.py
```

## Open Source And Dependency Notes

The MVP integrates `GazeFollower`, which is marked as `CC BY-NC-SA 4.0` in its GitHub repository. This matches the current non-commercial, community prototype stage.

GazeFollower repository: https://github.com/GanchengZhu/GazeFollower

If the project later needs commercial distribution, app-store packaging, or a broader license, the gaze-tracking dependency and license boundary must be revisited.

## Roadmap

See [docs/ROADMAP.en.md](docs/ROADMAP.en.md).

Key directions include gaze latency calibration, OCR for scanned PDFs, tray/floating-window modes, reader profiling, attention nudges, stronger privacy boundaries, and community plugins.

## Tests

```powershell
conda activate marginmind
python -m tests.smoke_test
python -m tests.read_scope_test
node --check static\app.js
python -m pip check
```
