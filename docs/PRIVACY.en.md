# Privacy And Safety

MarginMind is currently a local MVP. Because it touches webcam access, reading documents, gaze traces, and AI APIs, the default principle is: keep local data local and avoid collecting data that is not needed.

## What It Does Not Do

- It does not record audio.
- It does not upload camera frames.
- It does not store raw camera frames in the project directory.
- It should not publish `.env`, API keys, `storage/`, or logs to the repository.

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

These files may contain private reading material and behavioral data. Do not commit them to GitHub.

## What Is Sent To AI

When generating notes, the app submits:

- Pages actually read in the current session.
- Original text context for those pages.
- Per-page gaze attention summaries.
- Text explicitly selected by the user.
- The user's note request.

The app does not send camera frames or audio. Original text is context; the note should prioritize gaze focus and explicit selections.

## Camera Indicator Light

Many laptop webcam lights are hardware or OS-level privacy indicators. Generic Web/Python code usually cannot turn the light off while continuing to use the camera. The MVP handles this by stopping gaze tracking and releasing the camera when tracking is no longer needed.

## Pre-Publish Checklist

Before publishing to GitHub, verify that:

- `.env` is not committed.
- `storage/` is not committed.
- `server*.log` is not committed.
- Real API keys are not present in README files, issues, commits, or screenshots.
- Private reading documents are not committed.
- Local drafts are not committed; public docs should use sanitized descriptions.

If an API key was ever exposed publicly, revoke it immediately and create a new one.
