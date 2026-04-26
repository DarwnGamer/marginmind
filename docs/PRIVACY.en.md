# Privacy And Safety

MarginMind is currently a local MVP. Because it touches webcam access, reading documents, gaze traces, and AI APIs, the default principles are local-first storage, minimal collection, and transparent submission.

## Data Boundary

- It does not record audio.
- It does not upload camera frames.
- Raw camera frames are not stored in the project directory.
- The public repository uses sample environment configuration; runtime data stays local.

## What Is Stored Locally

Runtime data is stored under `storage/`:

- Uploaded documents.
- Parsed document text.
- Reading session events.
- Gaze sample coordinates and timestamps.
- Page text-box layouts.
- Internal AI context: `ai_context.json`.
- AI prompt: `ai_prompt.md`.
- Final notes: `notes.md`.

These files may contain private reading material and behavioral data, so they are treated as local runtime data.

## What Is Sent To AI

When generating notes, the app submits:

- Pages actually read in the current session.
- Original text context for those pages.
- Per-page gaze attention summaries.
- Text explicitly selected by the user.
- The user's note request.

Submitted content excludes camera frames and audio. Original text is context; the note prioritizes gaze focus and explicit selections.

## Camera Indicator Light

Many laptop webcam lights are hardware or OS-level privacy indicators. The MVP releases the camera by stopping gaze tracking; indicator state is managed by the operating system or device firmware.

## Maintainer Release Review

Before a public release, maintainers can review:

- Repository content uses `.env.example` as sample configuration.
- `storage/` and `server*.log` remain local runtime data.
- README files, issues, commits, and screenshots use sanitized content.
- Private reading documents, local drafts, and debug output remain local.

Credential rotation follows provider guidance.
