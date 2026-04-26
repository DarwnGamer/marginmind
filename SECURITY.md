# Security Policy

## Reporting

Public reports work best with sanitized examples, synthetic documents, and redacted logs.

Sensitive reports can use maintainer contact channels when they are published.

## Local Credentials

The project loads provider credentials from `.env`, which is treated as local configuration. Credential rotation follows the relevant provider guidance.

## Runtime Data

The `storage/` directory may contain uploaded files, parsed text, gaze samples, AI prompts, internal AI context, and generated notes. It is treated as local runtime data.
