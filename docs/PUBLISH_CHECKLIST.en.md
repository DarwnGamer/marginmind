# GitHub Pre-Publish Checklist

## Repository Scope

- Use `.env.example` as sample configuration.
- Keep `storage/`, `server*.log`, uploaded documents, gaze samples, and debug output as local runtime data.
- Use sanitized content in README files, issues, commit messages, and screenshots.
- Keep local drafts, personal notes, and unpolished idea documents local.

## Recommended Flow

1. Use git instead of manually zipping and uploading the whole folder.
2. Run the pre-publish check:

   ```powershell
   python scripts\pre_publish_check.py
   ```

3. Check `git status --ignored` and confirm local runtime data is ignored.
4. Credential rotation follows provider guidance.

## Files That Should Be Published

- `app/`
- `static/`
- `tests/`
- `docs/`
- `.github/`
- `README.md`
- `README.en.md`
- `.env.example`
- `.gitignore`
- `environment.yml`
- `requirements.txt`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `NOTICE.md`

## Local Runtime Data

- `.env`
- `storage/`
- `server.err.log`
- `server.out.log`
- Local drafts, personal notes, or unpolished idea documents
- Any private uploaded documents
- Any API responses or debug logs containing private text
