# Project Idea And External Feedback

This document separates two sources: the project initiator's original product direction, and selected external AI feedback that is useful for public discussion. It is a public open-source summary, not a raw copy of the private idea note.

## Originality Boundary

This repository should not claim that the whole direction is legally original or novel. Public work already exists around eye-tracking-enabled PDF readers, gaze-assisted note anchoring, real-time gaze-to-web-text mapping, and eye-tracking research for reading comprehension and learning. MarginMind therefore does not claim that "gaze tracking plus reading analysis" was first proposed here.

What should be attributed clearly is the project-specific plan proposed by the project initiator: a study-reading note tool that combines reading-page content positioning, timestamped gaze traces, page-level source-text mapping, the user's note request, and later AI generation into a runnable MVP for open-source collaboration.

## Original Direction From The Project Initiator

- Build for study-oriented reading, using webcam-based gaze tracking to record the reading process and help AI generate notes, revisit suggestions, or self-test questions that better reflect how the document was actually read.
- AI notes should not simply summarize the whole text. They should consider the user's note request, reading dwell, quick skips, rereads, and explicit annotations.
- Users should be able to state their goal before reading, because note-taking may support review, exams, close reading, structure building, or finding weak spots.
- Gaze traces should include timestamps and be mapped to reading-page content, producing review cues such as where dwell was longer, what may have been skimmed quickly, and where it happened.
- Reading-page numbers may differ from source-document page numbers, so the app needs stable mapping from reader pages to source text ranges.
- Reader profiles should form gradually through reading goals, settings, annotations, and review feedback instead of a heavy upfront questionnaire.
- The product should avoid making users dependent on AI. AI should suggest, point out blind spots, and encourage restatement and thinking instead of flattering or replacing learning.
- Attention nudges matter, but they must be cautious. Long dwell may mean distraction or valuable thinking, so nudges should be low-frequency, optional, and non-disruptive.
- Notes do not have to be traditional outlines. Depending on goals and reader profile, they may become question cards, revisit lists, concept relations, self-tests, or other formats.
- Mouse and keyboard actions should participate in reading, such as selecting text to tell AI to pay extra attention, while still supporting immersive low-interruption reading.
- Privacy and safety should be considered from the start. Camera frames should stay out of the upload flow, audio is off by default, and public collaboration should avoid personal material.
- The reading process should not add too much noise or setup burden. Technical choices should minimize hardware load and startup friction.
- Long-term gaze tracking may cause eye fatigue, but this should not be rushed into a "fatigue detector." A safer first step is sampling-duration visibility, rest reminders, opt-out controls, and camera-off modes; health-related wording must not be treated as medical judgment.
- The long-term product form may become a tray app, floating window, or lighter entry point instead of a full tool flow every time.
- The project should start as an MVP and then grow through GitHub open-source collaboration, with careful attention to dependency licenses.

## Concrete Implementation Plan Proposed By The Project Initiator

The original plan was not simply "let AI summarize a document." It first structures the reading process, then gives structured reading evidence to AI:

- Identify or render the reading page to obtain text fragments that correspond to screen positions.
- Preserve position, page number, and start/end information for each text fragment, so the app can later map reader pages to source-document fragments.
- Collect timestamped gaze traces and overlap them with page text positions to infer which regions had longer dwell and which regions may have been skimmed quickly.
- Save page-level reading-behavior summaries, such as page number, dwell regions, possible skimmed regions, dwell duration, and explicit user annotations.
- During note generation, avoid sending the whole source document indiscriminately. Submit only the read-scope source text, behavior summary, and the user's note request.
- Because reader pages and source pages may not match one-to-one, preserve page-level start/end content or fragment mapping before sending context to AI.

The current MVP adopts the main idea while changing the engineering path: instead of generic screenshot OCR or a "special image" representation, it prioritizes rendered PDF pages plus PyMuPDF text-box extraction. The frontend submits real screen-space text boxes, and the backend overlaps them with GazeFollower coordinates and timestamps. This is more stable, easier to test, and easier for an open-source project to maintain.

## How The Current MVP Implements It

- Starts as a local-first Web MVP supporting PDF, DOCX, TXT, and Markdown uploads.
- Uses fixed paged reading to reduce coordinate drift caused by scrolling.
- Shows original rendered PDF pages while extracting text boxes for gaze-to-text matching.
- Records page views, layout changes, selected text, and gaze samples to estimate the actual read scope.
- Submits only evidence-backed read pages during note generation.
- Treats explicit text selection as a user action and gaze dwell as a system observation cue, avoiding direct claims that gaze coordinates equal understanding.
- Stops gaze tracking and releases the camera before note review.

## Module Status Boundaries

- Implemented: local Web reader, fixed page turns, PDF page rendering and text-box extraction, GazeFollower sampling, read-scope trimming, program-generated evidence panel, and AI-assisted note body.
- Partial/fallback capability: without gaze, the app can still use source text, page dwell, and selected text, but this is not a complete manual-only mode yet.
- Not implemented: long-term reader profiling, mind-wandering nudges, fatigue detection, pre-generation heatmap preview, full evidence confirmation, OCR, formula/table/image-region recognition, tray/floating-window/browser-extension forms, local models, and session-management UI.
- Under research: eye comfort, reading-training positioning, and whether gaze tracking adds enough value over scroll/manual baselines.

## External Feedback Addendum

- Webcam-based gaze tracking is better suited for page-level, region-level, or paragraph-level evidence than word-level claims.
- Gaze dwell does not equal understanding or attention. Long dwell may come from reflection, confusion, distraction, or environmental noise.
- Fixed paged reading helps stabilize coordinate mapping in the MVP, but future UX should explore more natural scrolling, web, and PDF reading modes.
- Camera access can create psychological pressure even when frames stay local, so the app needs clearer status, one-click stop, and camera-off modes.
- Before note generation, the app could show explicit user actions, system observation cues, and evidence gaps so users can confirm what AI will use.
- With the camera off, the system should degrade to a manual-only mode based on selections, annotations, questions, and user feedback.
- AI is better framed as a reading partner: helping users review, ask questions, and find blind spots instead of directly replacing summary work.

## Objective View On Camera Necessity

The external critique raises a fair question: if scrolling behavior, dwell time, and manual annotations are enough to generate good results, camera access adds privacy pressure, startup friction, and engineering complexity. That question should not be waved away.

Keeping the camera path is also reasonable. MarginMind is not meant to be just another PDF annotation plus AI summary tool. The possible value of webcam gaze is lower-interruption reading-behavior capture for long-term reader profiling, reading review, and reading training. Users do not always annotate explicitly, and explicit annotations only capture what users are willing to mark. If gaze can provide extra behavioral cues at low enough cost, it may be more natural than requiring frequent manual marking.

The objective positioning is therefore not "the camera is definitely necessary." It is "camera-based reading behavior capture is the project's experimental differentiator." It must be compared with camera-off baselines: on the same document, source text + scroll/dwell + manual annotations versus the same inputs plus gaze. The project should compare note usefulness, revisit-suggestion accuracy, user burden, and privacy discomfort. If the lift is small, camera should become optional; if the lift is meaningful, the project should strengthen the reading-behavior quantification and training direction instead of only advertising AI note generation.

On whether to remove AI note generation: this does not have to be binary. Removing notes entirely would make the product closer to a reading-training tool, but notes remain the easiest entry point for users to understand. A safer direction is to treat notes as one output form while increasing the weight of reading review, evidence panels, revisit suggestions, self-test questions, and reader profiling.

## Good Future Issues

- Paragraph-level or region-level gaze evidence instead of word-level claims.
- Evidence preview and user confirmation before generation.
- Camera-off baseline experiments: compare source text + scroll/dwell + manual annotations with the same inputs plus gaze.
- Reading-behavior quantification and reader profiling: turn gaze, dwell, page turns, annotations, and review feedback into long-term explainable reading patterns, not only one-off note generation.
- Explicit annotations, question buttons, and important/confusing markers.
- Low-interruption attention nudges and reading review.
- Camera-off and manual-only modes.
- Eye-comfort research: sampling duration, rest reminders, opt-out controls; no medicalized fatigue judgment for now.
- More natural scroll-based reading.
- Tray, floating-window, or browser-extension forms.
- OCR, formula, table, and image-region recognition.
- Feedback loops after users review generated notes.
- Local model options or stronger privacy-preserving modes.

## Related Public Work

These references help define the boundary between existing public directions and this project's concrete plan. They are not claimed to be identical to MarginMind:

- [PeyeDF](https://arxiv.org/abs/1904.12152): an eye-tracking-enabled PDF reader that integrates PDF reading behavior and gaze data, with annotation, tagging, and collaboration support.
- [GAVIN](https://arxiv.org/abs/2104.00870): uses gaze and machine learning to implicitly anchor voice notes to text fragments in digital documents.
- [EyeLiveMetrics](https://arxiv.org/abs/2601.02044): a browser plugin that maps raw gaze coordinates to web text in real time and calculates word/paragraph-level reading metrics.
- [Feedback beyond accuracy](https://pmc.ncbi.nlm.nih.gov/articles/PMC10084433/): discusses eye-tracking metrics as indirect feedback about reading comprehension and interest, while reminding that gaze and cognitive state are not a simple equivalence.
