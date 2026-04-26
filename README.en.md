# MarginMind / 澜页: Gaze-Aware AI Reading Notes

> Statement: the project initiator provided the product idea, requirements direction, and testing feedback; the current MVP implementation, debugging, and the following documentation were mainly completed with Codex.

[中文](README.md)

<p align="center">
  <img src="static/marginmind-icon.svg" width="96" height="96" alt="MarginMind icon">
</p>

MarginMind is an open-source, local-first AI reading-notes MVP for study-oriented reading. A user uploads a document, reads it in a fixed paged reader, and the app uses webcam-based gaze tracking to estimate which page regions were actually attended to. Notes are generated from the read pages, gaze evidence, explicit text selections, and the user's note request.

Keywords: AI notes, reading notes, study notes, gaze tracking, eye tracking, PDF reader, document notes, learning assistant.

> This project is a non-commercial open-source prototype. Data is stored locally by default; audio and camera frames are outside the upload flow. Public contributions use sample configuration and sanitized material.

## Why This Name

The Chinese name “澜页” suggests attention rippling across a page. It is not just an eye-coordinate logger; it tries to turn pauses, skims, and rereads into reviewable reading traces. `MarginMind` combines `Margin` (page margin, annotation space, reading traces) and `Mind` (attention and thinking), leaving room for future reader profiling, review suggestions, attention nudges, and non-traditional note formats.

## Motivation

The original idea was a note-taking tool for learning: while reading, the webcam tracks gaze so the AI can understand where attention went and generate notes that reflect the actual reading process.

The product is designed to keep readers active: AI provides suggestions, identifies blind spots, and supports reflection while leaving room for the user's own thinking. Gaze traces are best treated as review cues; explicit selections, annotations, questions, and feedback are more reliable user actions.

## Community

MarginMind is an early MVP. Contributors interested in gaze tracking, document parsing, frontend/backend engineering, privacy and security, usability design, documentation, and open-source governance are welcome. Issues, docs, tests, reproducible bug reports, and small PRs are good starting points.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution notes, [docs/ROADMAP.en.md](docs/ROADMAP.en.md) for planned work, and [docs/IDEA_AND_FEEDBACK.en.md](docs/IDEA_AND_FEEDBACK.en.md) for the project direction and feedback summary.

## Current Features

- Upload `.pdf`, `.docx`, `.txt`, and `.md` files.
- Fast upload path: save file and metadata first; defer heavier parsing.
- Fixed paged reader with scroll-free pages, keeping gaze coordinates aligned with page positions.
- Page turning works with buttons, arrow keys, PageUp/PageDown, space, and the mouse wheel; wheel turns are throttled to avoid layout noise during rapid scrolling.
- PDF pages are rendered from the original PDF; text boxes are extracted from the same page for gaze matching.
- PDF whitespace is cropped to enlarge the readable content; after zooming, the frontend resubmits real screen-space text boxes.
- Local gaze tracking via `GazeFollower`.
- When notes are generated, gaze tracking is stopped and the camera is released.
- Page changes and zoom changes are treated as layout changes; nearby transient gaze samples are filtered to reduce latency errors.
- Rapid continuous flipping remains a preview interaction; a page enters the AI submission scope after stable dwell time, valid gaze, or an explicit selection.
- Only pages actually read in the session are submitted to AI.
- Results begin with a program-generated evidence panel, followed by an AI-assisted note body. Gaze dwell only informs review suggestions and self-test questions; it is not treated as proof of understanding or neglect.
- AI providers can be configured through environment variables; local rules are used when API credentials are absent.

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
├─ .env.example            # Sample environment template
└─ README.md               # Chinese README
```

Runtime files are intentionally ignored:

- `storage/`: uploaded files, sessions, gaze samples, internal AI context.
- `server*.log`: local server logs.
- `.env`: local environment configuration.

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

Stop the backend:

- If the PowerShell window running `uvicorn` is still open, press `Ctrl+C`.
- If the window was closed but port `8000` is still occupied, stop the process that owns that port:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object -ExpandProperty OwningProcess |
  ForEach-Object { Stop-Process -Id $_ }
```

Leave the conda environment:

```powershell
conda deactivate
```

## AI Provider Configuration

Copy `.env.example` to `.env` and fill in local provider configuration:

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

The copied `.env` file is loaded by the local service and remains a local configuration file.

## Usage

1. Upload a document.
2. Describe what kind of notes you need.
3. Start gaze tracking and finish GazeFollower calibration.
4. Return to the browser and read in the fixed paged reader. Use buttons, arrow keys, PageUp/PageDown, space, or the mouse wheel to turn pages.
5. Optionally select text as explicit attention markers.
6. Generate notes. The app stops gaze tracking before note generation.
7. The result page shows the pages submitted to AI, so the output can be checked against the actual read scope.

## Privacy And Safety

- No audio recording.
- No camera frame upload.
- Gaze samples, uploaded documents, AI prompts, and internal context are stored locally in `storage/`.
- Hardware camera indicator lights are usually managed by the operating system or device firmware; stopping gaze tracking releases the camera.
- Public issues, pull requests, and screenshots use sanitized material by default.

See [docs/PRIVACY.en.md](docs/PRIVACY.en.md).

Maintainers can use [docs/PUBLISH_CHECKLIST.en.md](docs/PUBLISH_CHECKLIST.en.md) and run:

```powershell
python scripts\pre_publish_check.py
```

## Open Source And Dependency Notes

The MVP integrates `GazeFollower`, which is marked as `CC BY-NC-SA 4.0` in its GitHub repository. MarginMind is maintained as a non-commercial, community-oriented research and learning tool.

GazeFollower repository: https://github.com/GanchengZhu/GazeFollower

Contributions and derivative work should treat the gaze-tracking dependency boundary as non-commercial.

## Roadmap

See [docs/ROADMAP.en.md](docs/ROADMAP.en.md) and [Project Idea And External Feedback](docs/IDEA_AND_FEEDBACK.en.md).

Key directions include gaze latency calibration, OCR for scanned PDFs, tray/floating-window modes, reader profiling, attention nudges, active annotation workflows, eye-comfort research (not implemented, not medical judgment), stronger privacy boundaries, and community plugins.

## Tests

```powershell
conda activate marginmind
python -m tests.smoke_test
python -m tests.read_scope_test
node --check static\app.js
python -m pip check
```
