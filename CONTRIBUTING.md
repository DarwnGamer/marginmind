# Contributing

Thanks for considering contributing to MarginMind / 澜页.

MarginMind is an early MVP for gaze-aware reading notes. Careful review, focused issues, small pull requests, tests, and documentation improvements are especially valuable.

中文说明：澜页是一个面向视线感知阅读笔记的早期 MVP。欢迎通过代码审阅、问题复现、小范围 PR、测试和文档改进一起把它变得更可靠。

## Before You Contribute

- Use sample configuration, synthetic documents, and sanitized logs in public contributions.
- Treat camera access, gaze samples, uploaded documents, prompts, and local storage as privacy-sensitive surfaces.
- Treat the current gaze-tracking dependency boundary as non-commercial.

## Useful Commands

```powershell
conda activate marginmind
python -m tests.smoke_test
python -m tests.read_scope_test
node --check static\app.js
python -m pip check
```

## Areas That Need Help

- Code review and architecture cleanup.
- Gaze latency calibration.
- OCR for scanned PDFs.
- Better evidence visualization.
- Cross-platform testing.
- Local/offline AI provider support.
- UI/UX around calibration and reading review.
- Privacy, security, and open-source governance.

中文方向：视线追踪延迟校准、PDF/OCR、证据可视化、跨平台测试、本地模型、校准与阅读体验、隐私安全、开源治理。
