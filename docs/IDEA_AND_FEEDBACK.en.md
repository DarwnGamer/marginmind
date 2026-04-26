# Project Idea And External Feedback

This document separates two sources: the project initiator's original product direction, and selected external AI feedback that is useful for public discussion. It is a public open-source summary, not a raw copy of the private idea note.

## Original Direction From The Project Initiator

- Build for study-oriented reading, using webcam-based gaze tracking to record the reading process and help AI generate notes that better reflect how the document was actually read.
- AI notes should not simply summarize the whole text. They should consider the user's note request, reading dwell, quick skips, rereads, and explicit annotations.
- Users should be able to state their goal before reading, because note-taking may support review, exams, close reading, structure building, or finding weak spots.
- Gaze traces should include timestamps and be mapped to reading-page content, producing evidence such as what was focused on, what was skimmed, and where it happened.
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

## How The Current MVP Implements It

- Starts as a local-first Web MVP supporting PDF, DOCX, TXT, and Markdown uploads.
- Uses fixed paged reading to reduce coordinate drift caused by scrolling.
- Shows original rendered PDF pages while extracting text boxes for gaze-to-text matching.
- Records page views, layout changes, selected text, and gaze samples to estimate the actual read scope.
- Submits only evidence-backed read pages during note generation.
- Treats explicit text selection as a user action and gaze dwell as a system observation cue, avoiding direct claims that gaze coordinates equal understanding.
- Stops gaze tracking and releases the camera before note review.

## External Feedback Addendum

- Webcam-based gaze tracking is better suited for page-level, region-level, or paragraph-level evidence than word-level claims.
- Gaze dwell does not equal understanding or attention. Long dwell may come from reflection, confusion, distraction, or environmental noise.
- Fixed paged reading helps stabilize coordinate mapping in the MVP, but future UX should explore more natural scrolling, web, and PDF reading modes.
- Camera access can create psychological pressure even when frames stay local, so the app needs clearer status, one-click stop, and camera-off modes.
- Before note generation, the app could show explicit user actions, system observation cues, and evidence gaps so users can confirm what AI will use.
- With the camera off, the system should degrade to a manual-only mode based on selections, annotations, questions, and user feedback.
- AI is better framed as a reading partner: helping users review, ask questions, and find blind spots instead of directly replacing summary work.

## Good Future Issues

- Paragraph-level or region-level gaze evidence instead of word-level claims.
- Evidence preview and user confirmation before generation.
- Explicit annotations, question buttons, and important/confusing markers.
- Low-interruption attention nudges and reading review.
- Camera-off and manual-only modes.
- Eye-comfort research: sampling duration, rest reminders, opt-out controls; no medicalized fatigue judgment for now.
- More natural scroll-based reading.
- Tray, floating-window, or browser-extension forms.
- OCR, formula, table, and image-region recognition.
- Feedback loops after users review generated notes.
- Local model options or stronger privacy-preserving modes.
