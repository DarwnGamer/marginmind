# AI Collaboration Development Record

This document records a real non-developer + AI coding collaboration experience for future contributors. It is not a universal method, only a retrospective from how this project came into being.

## What Happened

The project initiator first provided a product idea: use webcam-based gaze tracking during study reading, then let AI generate notes that better reflect the actual reading trace. In an earlier attempt, this high-level direction alone did not produce usable software.

In the later attempt, the project initiator added a more concrete implementation plan and technical-selection principles:

- Reading pages should first be identified or rendered into text regions that correspond to screen positions.
- Gaze traces must have timestamps and be overlappable with text regions.
- The system should save page-level reading-behavior summaries, then combine them with source text and the user's note request for AI.
- Technical choices should reduce setup burden, reduce reading-process noise, and respect open-source license boundaries.
- Gaze tracking should first try GazeFollower.
- Build an MVP first, then open-source it on GitHub for collaboration.

Within those clearer constraints, Codex turned the plan into code: a FastAPI backend, fixed paged reader, PDF rendering and text-box extraction, GazeFollower sampling, evidence panel, and AI-assisted note generation. Multiple rounds of testing and user feedback then corrected issues in startup latency, camera release, page-turn latency, read-scope trimming, mouse-wheel page turns, and evidence presentation.

## Was It Only A Model Upgrade

It should not be reduced to a model upgrade. A stronger model and better local tooling mattered, but the working MVP also depended on several other factors:

- The project initiator moved from "what I want" toward "how it might work": page text positioning, gaze timestamps, trace overlap, page-level mapping, and AI input structure.
- Technical choices narrowed an open problem into executable boundaries: local Web MVP, GazeFollower, common document formats first, and low setup friction.
- The user kept testing the software and reporting concrete failures: slow startup, camera release, page-turn delay, oversized AI submission scope, mouse-wheel page turns, and mixed evidence/notes.
- Codex had local code access, command execution, file editing, and tests, so abstract product ideas could repeatedly be pushed into a runnable state.
- The project did not treat AI output as final truth; tests, evidence panels, and documentation boundaries were used to keep risk visible.

A more accurate summary is: model capability improved execution, but clear implementation hypotheses, technical boundaries, user feedback, and verifiable checks were what made this attempt work.

## Takeaways For Non-Developers

If you are not a programmer but want to prototype a less-developed product idea with AI, the useful move may not be a perfect prompt. It may be providing a logically plausible data path:

- Describe the real use case, not only the feature name.
- Explain the data path: what enters the system, what it becomes in the middle, and who consumes it at the end.
- State technical constraints: local or cloud, privacy concerns, setup burden, license boundaries, and which formats come first.
- Let AI adjust implementation details while preserving the product hypothesis.
- Ask AI to run tests or produce observable verification after changes.
- Keep human judgment on experience: what feels unnatural, what feels untrustworthy, and what has drifted away from the original goal.

In this workflow, AI is closer to a fast engineering collaborator than a machine that invents a complete product from nothing. A non-developer's value is not only the first spark of an idea, but the continuing supply of use cases, boundaries, trade-offs, and acceptance criteria.

## Risks

- A concrete plan does not prove product value; real user testing is still needed.
- AI-generated code can hide errors and should be improved through tests, review, and public collaboration.
- Features involving cameras, reading behavior, and learning state should avoid overclaiming, especially psychological or medical claims.
- Documentation should separate "implemented," "partial," "under research," and "future direction" so contributors understand the actual project state.

## Related References

- [LLMs' Reshaping of People, Processes, Products, and Society in Software Development](https://arxiv.org/abs/2503.05012): early users report that LLMs reduce repetitive work and accelerate debugging, while human judgment, layered verification, and safe integration remain necessary.
- [The Use of AI in Software Engineering](https://www.mdpi.com/2078-2489/15/6/354/html): surveys AI use across testing, maintenance, requirement extraction, vulnerability detection, and software engineering education.
- [Human-AI Collaboration in Software Engineering](https://arxiv.org/abs/2312.10620): discusses capabilities, limits, and practical experience in human-AI software engineering collaboration.
