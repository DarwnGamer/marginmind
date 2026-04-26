# Roadmap

This roadmap combines the original idea, MVP tradeoffs, and issues discovered during implementation.

## Near-Term Priorities

- Better gaze latency calibration: different machines, webcams, and GazeFollower filters introduce different delays.
- More transparent evidence display: show which pages were submitted, which snippets were considered focus, and how strong the evidence is.
- Better GazeFollower startup UX: model warmup, clearer progress, and handling calibration-window focus failures.
- Reading heatmap preview: let users inspect gaze focus regions before generating notes.
- Error recovery: clearer actions for camera conflicts, calibration failures, and AI-provider errors.

## Document And Reading Support

- OCR for scanned PDFs: the current MVP works best with text-based PDFs.
- Image/formula/table markers: non-text regions should be marked and passed to AI with clear labels.
- Better page mapping: AI text pages may differ from reading pages, so reading-page-to-source-text mapping should become more robust.
- Section-based long reading: generate notes per section and merge them into a global note.

## User Experience

- Tray or floating-window mode: open only when needed.
- Reading modes: immersive no-interruption mode, active-selection mode, light reminder mode.
- Mind-wandering nudges: must be careful and optional, because pauses may be valuable thinking rather than distraction.
- Reader profile: infer note preferences through onboarding, settings, and feedback rather than a heavy questionnaire.
- Review interaction: users can mark notes as accurate, misread, or incomplete to improve later prompts and thresholds.

## Privacy And Safety

- Local data management UI: view, export, and delete sessions.
- Pre-submit preview: show pages and evidence before sending to AI.
- Local model option: explore note generation without external APIs.
- Least privilege: keep webcam access limited to the reading-sampling phase.

## Open Collaboration

- Code review and engineering cleanup: experienced contributors are welcome to review architecture, boundaries, and tests.
- Low-barrier tasks: split reproducible bugs, documentation edits, threshold tuning, UI copy, and test fixtures into beginner-friendly issues.
- Pluggable modules: gaze tracking, OCR, AI providers, note templates.
- Contribution guide and issue templates.
- Cross-platform testing: Windows, macOS, Linux.
- License review: GazeFollower is suitable for the current non-commercial stage; broader future use requires reevaluation.
