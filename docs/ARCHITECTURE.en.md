# Architecture

## Data Flow

1. The user uploads a document.
2. The backend stores the source file and fast metadata.
3. The reader displays the original document page by page.
4. The frontend records real screen-space text boxes for the current page.
5. The GazeFollower worker samples gaze coordinates and timestamps.
6. The backend combines page-view timeline, layout changes, gaze samples, and text boxes into an attention summary.
7. During note generation, only pages that were actually read are selected.
8. The backend builds an internal AI context and calls the configured AI provider or the local fallback.
9. The frontend displays only the final user-facing notes.

## Key Constraints

- The reader does not scroll, so gaze coordinates remain mappable to the page.
- After zooming or page changes, screen-space text boxes must be resubmitted.
- Gaze samples near zoom/page changes are ignored to reduce latency errors.
- Rapid continuous flipping does not count as reading.
- The program generates an evidence panel before appending the AI-assisted note body. Explicit selections, annotations, and user requests are explicit user actions; gaze dwell is only a review cue, not proof of understanding, attention, or neglect.

## Module Responsibilities

- `app/main.py`: API routes, sessions, gaze start/stop, note-generation entry point.
- `app/gaze_worker.py`: runs GazeFollower in a separate process.
- `app/document_renderer.py`: PDF rendering, whitespace cropping, text-box extraction.
- `app/attention.py`: overlaps gaze samples with page text boxes and computes attention duration.
- `app/note_generator.py`: builds AI context and prompts, calls providers.
- `static/app.js`: frontend state, paged reader rendering, layout submission, result display.
