# 澜页 / MarginMind：视线追踪驱动的 AI 阅读笔记工具

> 声明：本项目由项目发起人提供产品想法、需求方向和测试反馈；当前 MVP 的代码实现、调试整理和以下文档主要由 Codex 完成。

[English](README.en.md)

<p align="center">
  <img src="static/marginmind-icon.svg" width="96" height="96" alt="澜页 / MarginMind 图标">
</p>

澜页是一个开源、本地优先的 AI 阅读笔记 MVP：用户上传文档后进行固定翻页式阅读，系统用摄像头视线追踪记录用户在每页真正关注的位置，再把“已阅读页原文上下文 + 视线证据 + 用户笔记需求”交给 AI 生成阅读笔记。

关键词：AI 笔记、阅读笔记、学习笔记、视线追踪、眼动追踪、PDF 阅读器、文档笔记、复习助手。

> 当前项目定位为非商业开源原型。数据默认保存在本地；音频和摄像头画面不进入上传流程。公开贡献使用示例配置和脱敏材料。

## 为什么叫澜页 / MarginMind

「澜页」取的是阅读时注意力像水纹一样落在页面上的意思：它不是单纯记录眼动坐标，而是把停顿、掠过、回看变成可回顾的阅读痕迹。`MarginMind` 里的 `Margin` 指页边、边注和阅读留下的旁注空间，`Mind` 指注意力与思考本身。这个名字给后续的用户画像、走神提醒、回看建议和非传统笔记形态都留了余地。

## 设计初衷

这个 MVP 面向学习阅读场景：在阅读时用摄像头追踪视线，让 AI 理解用户在哪些内容上停留、哪些内容一眼带过，最后生成更贴近真实阅读过程的笔记。

它的设计目标是让 AI 提供建议、指出盲区、帮助复盘，同时保留用户主动思考的位置。

## 社区共建

澜页目前处于早期 MVP 阶段，欢迎对视线追踪、文档解析、前后端工程、隐私安全、可用性设计和开源治理感兴趣的朋友共同建设。建议先从 issue、文档、测试、复现 bug 和小范围 PR 开始。

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)，后续计划见 [docs/ROADMAP.zh.md](docs/ROADMAP.zh.md)。

## 当前功能

- 支持上传 `.pdf`、`.docx`、`.txt`、`.md`。
- 上传时只保存文件和快速元信息，避免进入阅读前长时间解析。
- 浏览器固定翻页式阅读，采用无滚动页面，避免视线坐标和页面位置错位。
- PDF 阅读时显示原 PDF 页面渲染图；后台提取同页文字框用于和视线轨迹叠合。
- 自动裁掉 PDF 大块页边空白，放大正文；缩放后重新提交当前屏幕文字框。
- 使用 `GazeFollower` 进行本地摄像头视线追踪、校准和采样。
- 生成笔记时自动停止视线追踪并释放摄像头，方便用户核对笔记。
- 翻页和缩放会记录为布局变更，附近的短暂 gaze 样本会被过滤，降低延迟误判。
- 连续快速翻页会保持在预览状态；页面稳定停留、积累有效 gaze 或有主动选中文本后进入提交范围。
- 只把本次会话实际阅读过的页提交给 AI。
- 提交给 AI 的材料区分“原文上下文”和“视线证据”：原文只做背景，笔记主干优先依据视线重点和主动标注。
- 支持通过环境变量配置 AI provider；缺少 API Key 时回退到本地规则版。

## 项目结构

```text
marginmind/
├─ app/                    # FastAPI 后端、文档解析、视线分析、笔记生成
│  ├─ main.py              # API 入口与会话流程
│  ├─ gaze_worker.py       # GazeFollower 本地采样进程
│  ├─ attention.py         # gaze 样本与页面文字框叠合分析
│  ├─ document_parser.py   # PDF/DOCX/TXT/MD 文本解析
│  ├─ document_renderer.py # PDF 页面渲染、裁白边、文字框提取
│  ├─ note_generator.py    # AI provider/本地规则生成
│  └─ storage.py           # 本地存储工具
├─ static/                 # 前端上传页、固定翻页阅读器、结果页、图标
├─ tests/                  # smoke test 与阅读范围测试
├─ docs/                   # 公开说明、路线图、隐私与安全
├─ .github/                # issue 与 PR 模板
├─ environment.yml         # conda 环境
├─ requirements.txt        # pip 依赖
├─ .env.example            # 示例环境变量模板
└─ README.en.md            # 英文说明
```

本地运行会生成：

- `storage/`：上传文档、会话、gaze 样本、内部 AI 上下文。
- `server*.log`：服务日志。
- `.env`：本地环境配置。

这些是本地运行数据，不属于仓库内容。

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

## AI Provider 配置

复制 `.env.example` 为 `.env`，填写本地 provider 配置：

```powershell
Copy-Item .env.example .env
```

示例：

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

复制后的 `.env` 会被本地服务读取，并保持为本地配置文件。

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
- 摄像头硬件指示灯通常由系统或硬件管理；停止追踪会释放摄像头。
- 公开 issue、PR 和截图默认使用脱敏材料。

更多说明见 [docs/PRIVACY.zh.md](docs/PRIVACY.zh.md)。

维护者可参考 [docs/PUBLISH_CHECKLIST.zh.md](docs/PUBLISH_CHECKLIST.zh.md)，并运行：

```powershell
python scripts\pre_publish_check.py
```

## 开源与依赖提醒

当前 MVP 集成 `GazeFollower`。其 GitHub 仓库标注为 `CC BY-NC-SA 4.0`，本项目也按“非商业、开源共建、研究/学习工具”方向维护。

GazeFollower 仓库：https://github.com/GanchengZhu/GazeFollower

贡献和二次开发请按非商业用途理解相关依赖边界。

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
