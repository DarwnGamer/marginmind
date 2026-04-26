# GitHub 发布前清单

## 仓库范围

- 使用 `.env.example` 作为示例配置。
- `storage/`、`server*.log`、上传文档、gaze 样本和调试输出保持为本地运行数据。
- README、issue、commit message 和截图使用脱敏内容。
- 本地草稿、个人笔记和未整理的想法文档保持在本地。

## 建议流程

1. 使用 git 提交，而不是直接把整个文件夹压缩上传。
2. 运行发布检查脚本：

   ```powershell
   python scripts\pre_publish_check.py
   ```

3. 检查 `git status --ignored`，核对本地运行数据处于 ignored 状态。
4. 凭据轮换按服务商平台流程处理。

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

## 本地运行数据

- `.env`
- `storage/`
- `server.err.log`
- `server.out.log`
- 本地草稿、个人笔记或未整理的想法文档
- 任何上传过的个人文档
- 任何 API 返回或调试日志中包含个人文本的文件
