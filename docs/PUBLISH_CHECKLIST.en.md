# GitHub Pre-Publish Checklist

## Must Check

- Do not commit `.env`.
- Do not commit `storage/`.
- Do not commit `server*.log`.
- Do not commit private reading documents.
- Do not commit local drafts, personal notes, or unpolished idea documents.
- Do not commit real DeepSeek/OpenAI API keys.
- Do not expose keys in screenshots, README files, issues, or commit messages.

## Recommended Flow

1. Use git instead of manually zipping and uploading the whole folder.
2. Run the pre-publish check:

   ```powershell
   python scripts\pre_publish_check.py
   ```

3. Check `git status --ignored` and verify sensitive files are ignored.
4. Before the first public release, consider rotating any API key used during local testing.

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

## Local Files That Should Not Be Published

- `.env`
- `storage/`
- `server.err.log`
- `server.out.log`
- Local drafts, personal notes, or unpolished idea documents
- Any private uploaded documents
- Any API responses or debug logs containing private text
