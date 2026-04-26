# Security Policy

## Reporting

Please do not open public issues containing API keys, private documents, gaze data, screenshots with secrets, or local storage contents.

For now, report sensitive issues privately to the repository maintainer once contact information is added.

## Local Secrets

The project uses `.env` for API keys. `.env` is ignored by git. If a key is accidentally exposed, revoke it immediately and create a new one with the provider.

## Sensitive Runtime Data

The `storage/` directory may contain uploaded files, parsed text, gaze samples, AI prompts, internal AI context, and generated notes. It is ignored by git and should stay local.
