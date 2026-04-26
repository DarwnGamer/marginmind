# GitHub 发布前清单

## 必须确认

- 不提交 `.env`。
- 不提交 `storage/`。
- 不提交 `server*.log`。
- 不提交个人阅读文档。
- 不提交本地草稿、个人笔记或未整理的想法文档。
- 不提交真实 DeepSeek/OpenAI API key。
- 不在截图、README、issue、commit message 中展示 key。

## 建议流程

1. 使用 git 提交，而不是直接把整个文件夹压缩上传。
2. 运行发布检查脚本：

   ```powershell
   python scripts\pre_publish_check.py
   ```

3. 检查 `git status --ignored`，确认敏感文件处于 ignored 状态。
4. 首次公开前，建议在 API 平台轮换一次曾经在本地测试中使用过的 key。

## 当前应发布的核心文件

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

## 不应发布的本地文件

- `.env`
- `storage/`
- `server.err.log`
- `server.out.log`
- 本地草稿、个人笔记或未整理的想法文档
- 任何上传过的个人文档
- 任何 API 返回或调试日志中包含个人文本的文件
