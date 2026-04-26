# Roadmap

This roadmap combines the original idea, MVP tradeoffs, and issues discovered during implementation.

See also [Project Idea And External Feedback](IDEA_AND_FEEDBACK.en.md), which separates the project initiator's original direction from external feedback addenda.

## Near-Term Priorities

- Better gaze latency calibration: different machines, webcams, and GazeFollower filters introduce different delays.
- More transparent evidence display: the current result has a post-generation evidence panel; next steps are pre-generation preview, user confirmation, and clearer evidence separation.
- Better GazeFollower startup UX: model warmup, clearer progress, and handling calibration-window focus failures.
- Reading heatmap preview: let users inspect gaze focus regions before generating notes.
- Error recovery: clearer actions for camera conflicts, calibration failures, and AI-provider errors.

## Product Hypothesis Validation

- Camera necessity test: on the same document, compare source text + scroll/dwell + manual annotations with the same inputs plus gaze, measuring revisit suggestions, note usefulness, user burden, and privacy discomfort.
- Reading-behavior quantification: turn gaze, dwell, page turns, annotations, and review feedback into explainable reading patterns for reader profiling and reading training, not only one-off note generation.
- Positioning boundary: keep AI notes as an entry point, but avoid making the project only an automatic note tool; reading review, evidence panels, self-test questions, and revisit suggestions should become core experiences.
- Failure condition: if gaze does not add meaningful value over camera-off baselines, camera access should become optional rather than being kept only for differentiation.

## Document And Reading Support

- OCR for scanned PDFs: not implemented. The current MVP works best with text-based PDFs.
- Image/formula/table markers: not implemented. Non-text regions should be marked and passed to AI with clear labels.
- Better page mapping: AI text pages may differ from reading pages, so reading-page-to-source-text mapping should become more robust.
- Section-based long reading: generate notes per section and merge them into a global note.

## User Experience

- Tray or floating-window mode: not implemented. It should open only when needed.
- Reading modes: a full mode system is not implemented yet. Future modes may include immersive no-interruption mode, active-selection mode, and light reminder mode.
- Mind-wandering nudges: not implemented. They must be careful and optional, because pauses may be valuable thinking rather than distraction.
- Reader profile: long-term profiling is not implemented. Future work should infer preferences through onboarding, settings, and feedback rather than a heavy questionnaire.
- Review interaction: users can mark notes as accurate, misread, or incomplete to improve later prompts and thresholds.
- Active annotation workflow: selections, question clicks, highlights, and confusion markers should be explicit user actions; gaze should only provide auxiliary review cues.
- Non-traditional note formats: generate question cards, review lists, concept maps, counterargument lists, or other forms based on reading goals and user preferences.
- Lower setup friction: reduce startup steps and waiting time so users feel they can start reading immediately.
- Eye-comfort research: fatigue detection is not implemented and should not be rushed into medicalized judgment. Start with sampling-duration visibility, rest prompts, opt-out controls, and a camera-off mode, then decide from real testing.

## Reading Behavior Understanding

- Anti-dependency design: AI should help readers notice blind spots, ask questions, and restate ideas instead of waiting passively for answers.
- Mind-wandering versus thinking: long dwell may mean distraction or valuable reflection; nudges should be low-frequency, optional, and conservatively interpreted.
- Gradual reader profiling: infer preferences from reading goals, note style, explicit annotations, and review feedback instead of a heavy questionnaire.
- Mouse and keyboard participation: selection, clicking, annotation, shortcuts, and question buttons provide more reliable context than gaze alone.
- Explainable evidence: before note generation, show explicit user actions, system observation cues, and gaps so users know what the AI used.

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
- License boundary: GazeFollower is used for non-commercial research, learning, and open collaboration.
