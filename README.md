# 澜页 / MarginMind

[English](README.en.md)

<p align="center">
  <img src="static/icon.svg" width="96" height="96" alt="澜页 / MarginMind 图标">
</p>

澜页是一个面向阅读学习场景的本地 MVP：用户上传文档后进行固定翻页式阅读，系统用摄像头视线追踪记录用户在每页真正关注的位置，再把“已阅读页原文上下文 + 视线证据 + 用户笔记需求”交给 AI 生成阅读笔记。

> 当前项目处于非商业原型阶段。默认本地保存数据，不采集声音，不上传摄像头画面。请不要提交 `.env`、`storage/`、日志或个人阅读材料。

## 为什么叫澜页 / MarginMind

「澜页」取的是阅读时注意力像水纹一样落在页面上的意思：它不是单纯记录眼动坐标，而是把停顿、掠过、回看变成可回顾的阅读痕迹。`MarginMind` 里的 `Margin` 指页边、边注和阅读留下的旁注空间，`Mind` 指注意力与思考本身。这个名字给后续的用户画像、走神提醒、回看建议和非传统笔记形态都留了余地。

## 设计初衷

这个 MVP 来自一个阅读笔记工具想法：在学习阅读时，用摄像头追踪视线，让 AI 知道用户在哪些内容上停留、哪些内容一眼带过，最后生成更贴近真实阅读过程的笔记。

它刻意避免把 AI 设计成“全能总结器”。AI 应该给建议、指出盲区、帮助复盘，而不是只做恭维式总结，也不应该让用户在阅读学习时完全不动脑。

## 项目来源与共建邀请

这个项目由发起人提供阅读学习场景中的真实困惑、产品想法和简单实现方案；当前代码原型主要由 AI 辅助生成，并经过多轮人工反馈调整。它可以跑通 MVP，但还不应被视为成熟、充分审计或适合生产环境的软件。

发起人主要负责问题洞察、产品方向和使用体验反馈。后续希望邀请对视线追踪、文档解析、前后端工程、隐私安全、可用性设计、开源治理感兴趣的朋友共同建设。欢迎先从 issue、文档、测试、复现 bug 和小范围 PR 开始。

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，后续计划见 [docs/ROADMAP.zh.md](docs/ROADMAP.zh.md)。

## 当前功能

- 支持上传 `.pdf`、`.docx`、`.txt`、`.md`。
- 上传时只保存文件和快速元信息，避免进入阅读前长时间解析。
- 浏览器固定翻页式阅读，不允许滚动阅读，避免视线坐标和页面位置错位。
- PDF 阅读时显示原 PDF 页面渲染图；后台提取同页文字框用于和视线轨迹叠合。
- 自动裁掉 PDF 大块页边空白，放大正文；缩放后重新提交当前屏幕文字框。
- 使用 `GazeFollower` 进行本地摄像头视线追踪、校准和采样。
- 生成笔记时自动停止视线追踪并释放摄像头，方便用户核对笔记。
- 翻页和缩放会记录为布局变更，附近约 `0.8s` 的 gaze 样本会被忽略。
- 连续快速翻页不算已读页。页面需要稳定停留约 `3s`、或累计有效 gaze 约 `1s`、或有主动选中文本，才进入提交范围。
- 只把本次会话实际阅读过的页提交给 AI。
- 提交给 AI 的材料区分“原文上下文”和“视线证据”：原文只做背景，笔记主干优先依据视线重点和主动标注。
- 默认优先调用 DeepSeek API；未配置 API Key 时回退到 OpenAI 或本地规则版。

## 项目结构

```text
D:\note
├─ app/                    # FastAPI 后端、文档解析、视线分析、笔记生成
│  ├─ main.py              # API 入口与会话流程
│  ├─ gaze_worker.py       # GazeFollower 本地采样进程
│  ├─ attention.py         # gaze 样本与页面文字框叠合分析
│  ├─ document_parser.py   # PDF/DOCX/TXT/MD 文本解析
│  ├─ document_renderer.py # PDF 页面渲染、裁白边、文字框提取
│  ├─ note_generator.py    # DeepSeek/OpenAI/本地规则生成
│  └─ storage.py           # 本地存储工具
├─ static/                 # 前端上传页、固定翻页阅读器、结果页、图标
├─ tests/                  # smoke test 与阅读范围测试
├─ docs/                   # 公开说明、路线图、隐私与安全
├─ .github/                # issue 与 PR 模板
├─ environment.yml         # conda 环境
├─ requirements.txt        # pip 依赖
├─ .env.example            # 环境变量模板，不含密钥
└─ README.en.md            # 英文说明
```

本地运行会生成：

- `storage/`：上传文档、会话、gaze 样本、内部 AI 上下文。
- `server*.log`：服务日志。
- `.env`：本地 API key。

这些文件都不应提交到 GitHub。

## 安装与运行

```powershell
conda env create -f environment.yml
conda activate marginmind
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## API Key 配置

复制 `.env.example` 为 `.env`，填入自己的 key：

```powershell
Copy-Item .env.example .env
```

DeepSeek：

```text
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

OpenAI 可选：

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=
```

`.env` 已被 `.gitignore` 排除。不要把真实 key 写进 README、issue、截图或 commit。

## 使用流程

1. 上传阅读文档。
2. 填写本次笔记需求，例如“帮我找出核心概念、薄弱处和适合复习的问题”。
3. 点击“开始视线追踪”，完成 GazeFollower 校准。
4. 回到浏览器进行固定翻页式阅读。
5. 阅读时可用选中文字作为主动标注。
6. 点击“生成笔记”。系统会先停止视线追踪，再生成笔记。
7. 结果页会显示本次实际提交的页码，便于核对 AI 是否依据了你的阅读过程。

## 隐私与安全

- 不采集声音。
- 不上传摄像头画面。
- 原始 gaze 样本、上传文档、AI prompt 和内部上下文默认保存在本机 `storage/`。
- 摄像头硬件指示灯通常不能被通用软件单独关闭；停止追踪会释放摄像头。
- 公开仓库前请确认未包含 `.env`、`storage/`、日志、个人文档和原始想法草稿。

更多说明见 [docs/PRIVACY.zh.md](docs/PRIVACY.zh.md)。

发布到 GitHub 前请阅读 [docs/PUBLISH_CHECKLIST.zh.md](docs/PUBLISH_CHECKLIST.zh.md)，并运行：

```powershell
python scripts\pre_publish_check.py
```

## 开源与依赖提醒

当前 MVP 按原始设想集成 `GazeFollower`。其 GitHub 仓库标注为 `CC BY-NC-SA 4.0`，适合当前“非商业、开源共建、研究/学习工具”阶段。

GazeFollower 仓库：https://github.com/GanchengZhu/GazeFollower

后续如果项目需要商业化、上架或更宽松的许可分发，需要重新评估视线追踪依赖和许可证边界。

## 后续展望

见 [docs/ROADMAP.zh.md](docs/ROADMAP.zh.md)。

重点方向包括：更精细的 gaze 延迟校准、扫描版 PDF OCR、托盘/悬浮窗形态、用户画像与笔记风格、走神提醒、安全边界、社区插件化。

## 测试

```powershell
conda activate marginmind
python -m tests.smoke_test
python -m tests.read_scope_test
node --check static\app.js
python -m pip check
```
