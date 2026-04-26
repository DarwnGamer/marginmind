# Contributing

Thanks for considering contributing to MarginMind / 澜页.

MarginMind started from a product idea and simple MVP direction provided by the project initiator. The current codebase is an AI-assisted early prototype shaped by manual testing and feedback, so careful review and incremental improvement are especially valuable.

中文说明：澜页由项目发起人提供产品想法、MVP 方向和使用反馈，当前代码主要是 AI 辅助生成的早期原型。欢迎有经验的开发者、设计者、研究者和文档贡献者一起把它变得更可靠。

## Before You Contribute

- Do not commit API keys, `.env`, `storage/`, logs, uploaded documents, or gaze samples.
- Keep privacy-sensitive changes conservative by default.
- The current gaze dependency is non-commercial; avoid implying commercial readiness.

## Useful Commands

```powershell
conda activate marginmind
python -m tests.smoke_test
python -m tests.read_scope_test
node --check static\app.js
python -m pip check
```

## Areas That Need Help

- Code review and architecture cleanup for an AI-assisted prototype.
- Gaze latency calibration.
- OCR for scanned PDFs.
- Better evidence visualization.
- Cross-platform testing.
- Local/offline AI provider support.
- UI/UX around calibration and reading review.
- Privacy, security, and open-source governance.

中文方向：视线追踪延迟校准、PDF/OCR、证据可视化、跨平台测试、本地模型、校准与阅读体验、隐私安全、开源治理。
