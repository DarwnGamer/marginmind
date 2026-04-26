# External Review Notes

These notes summarize selected feedback from an external AI review. They are not final conclusions; they are discussion material for future contributors.

## Key Reminders

- Webcam-based gaze tracking is better suited for page-level, region-level, or paragraph-level evidence than word-level claims.
- Gaze dwell does not equal understanding or attention. Long dwell may come from reflection, confusion, distraction, or environmental noise.
- Gaze should be treated as a weak signal. Explicit selections, annotations, questions, question-button clicks, and review feedback should be treated as stronger evidence.
- Fixed paged reading helps the MVP keep coordinate mapping stable, but future UX should explore more natural scrolling, web, and PDF reading modes.
- Camera access can create psychological pressure even when frames stay local, so the app needs clearer status, one-click stop, and camera-off modes.
- AI should act more like a reading partner: helping users review, ask questions, and find blind spots instead of directly replacing summary work.

## Task-Shaped Directions

- Shift gaze hits from word-level interpretation to paragraph-level or region-level evidence.
- Before note generation, show strong signals, weak signals, and evidence gaps for user confirmation.
- Add a manual-only mode: with the camera off, notes can still be generated from selections, annotations, and questions.
- Add lightweight attention review: show long-dwell areas, skipped areas, explicit annotations, and possible revisit targets.
- Design low-interruption attention nudges: only prompt after prolonged lack of effective reading activity, and keep it optional.
- Rework default note output toward questions, revisit suggestions, and self-test cards rather than full summaries.
- Explore scroll-based reading: combine visible paragraphs, scroll speed, dwell time, and explicit annotations to estimate reading scope.

## Pitfalls To Avoid

- Interpreting gaze coordinates as proof of real attention or understanding.
- Letting gaze data override explicit user annotations and note requests.
- Sacrificing natural reading experience for tracking precision.
- Creating unnecessary privacy pressure with camera features.
- Letting AI only provide answers instead of prompting user restatement, judgment, and questions.
