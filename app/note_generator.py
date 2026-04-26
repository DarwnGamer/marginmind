from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception:
    pass


def generate_notes(
    document: dict[str, Any],
    analysis: dict[str, Any],
    note_goal: str,
    reader_profile: dict[str, Any] | None = None,
    use_ai: bool = True,
) -> dict[str, Any]:
    context = build_ai_context(document, analysis, note_goal, reader_profile or {})
    prompt = build_ai_prompt(context)

    if use_ai and os.getenv("DEEPSEEK_API_KEY"):
        try:
            notes = _generate_with_deepseek(prompt)
            return {"notes": notes, "provider": _deepseek_provider_name(), "ai_context": context, "ai_prompt": prompt}
        except Exception as exc:
            notes = _generate_local(document, analysis, note_goal, reader_profile or {})
            notes += f"\n\n> DeepSeek 调用失败，已回退到本地规则版：{exc}"
            return {"notes": notes, "provider": "local-fallback", "ai_context": context, "ai_prompt": prompt}

    if use_ai and os.getenv("OPENAI_API_KEY"):
        try:
            notes = _generate_with_openai(prompt)
            return {"notes": notes, "provider": "openai", "ai_context": context, "ai_prompt": prompt}
        except Exception as exc:
            notes = _generate_local(document, analysis, note_goal, reader_profile or {})
            notes += f"\n\n> OpenAI 调用失败，已回退到本地规则版：{exc}"
            return {"notes": notes, "provider": "local-fallback", "ai_context": context, "ai_prompt": prompt}

    return {
        "notes": _generate_local(document, analysis, note_goal, reader_profile or {}),
        "provider": "local",
        "ai_context": context,
        "ai_prompt": prompt,
    }


def build_ai_context(
    document: dict[str, Any],
    analysis: dict[str, Any],
    note_goal: str,
    reader_profile: dict[str, Any],
) -> dict[str, Any]:
    pages = []
    for page in document.get("pages", []):
        text = str(page.get("text") or "")
        pages.append(
            {
                "page_number": page.get("page_number"),
                "start_excerpt": _trim(text, 180),
                "end_excerpt": _trim(text[-220:], 180),
                "text": text,
            }
        )

    attention_pages = []
    total_gaze_seconds = 0.0
    focus_item_count = 0
    selection_count = 0
    for page in analysis.get("pages", []):
        total_gaze_seconds += float(page.get("total_gaze_seconds") or 0)
        focus_item_count += len(page.get("top_focus", []))
        selection_count += len(page.get("selections", []))
        attention_pages.append(
            {
                "page_number": page.get("page_number"),
                "total_gaze_seconds": page.get("total_gaze_seconds"),
                "top_focus": page.get("top_focus", [])[:10],
                "skimmed": page.get("skimmed", [])[:8],
                "selections": page.get("selections", [])[:8],
            }
        )

    return {
        "note_request": note_goal or "生成一份适合复习和继续思考的阅读笔记。",
        "reader_profile": reader_profile,
        "document": {
            "title": document.get("title") or "未命名文档",
            "filename": document.get("filename"),
            "page_count": len(pages),
            "pages": pages,
        },
        "attention": {
            "sample_count": analysis.get("sample_count"),
            "layout_count": analysis.get("layout_count"),
            "total_gaze_seconds": round(total_gaze_seconds, 2),
            "focus_item_count": focus_item_count,
            "selection_count": selection_count,
            "read_scope": analysis.get("read_scope", {}),
            "interpretation_policy": {
                "full_text_role": "context_only",
                "top_focus_role": "weak_attention_signal",
                "selection_role": "strong_explicit_attention_evidence",
                "skimmed_role": "possible_gap_or_low_attention",
                "low_confidence_rule": "If gaze evidence is sparse or inconsistent, say so and avoid overclaiming what the user focused on.",
            },
            "pages": attention_pages,
        },
    }


def build_ai_prompt(context: dict[str, Any]) -> str:
    return (
        "下面是澜页 MarginMind 给你的内部生成材料。请只输出给用户看的最终阅读笔记。\n\n"
        "硬性要求：\n"
        "1. 不要输出 JSON、内部字段名、系统提示词、页码边界标签或完整原文转储。\n"
        "2. 原文全文只用于理解上下文；不能把全文总结当成用户实际阅读重点。\n"
        "3. selections 是强证据，可以写成“你主动标注/选中”；top_focus 只是弱注意力信号，只能写成“系统观察到停留较多”。\n"
        "4. skimmed 只能写成“可能需要回看/可能一眼带过”，不能写成用户已经掌握；长时间停留也不能直接写成理解或专注。\n"
        "5. 如果 gaze 样本少、聚焦片段少或阅读证据不足，要在开头用一句话说明“视线证据有限”，并生成保守笔记。\n"
        "6. 可以用原文补充必要背景，但必须标注为“原文上下文补充”，不要让它盖过主动标注和保守的视线线索。\n"
        "7. 不要一味夸用户；指出可能忽略的内容和下一步行动。\n"
        "8. 输出中文 Markdown，结构固定为：阅读证据概况、主动标注与视线线索、原文上下文补充、可能忽略/需回看、自测问题。\n\n"
        "内部材料如下：\n"
        "```json\n"
        f"{json.dumps(context, ensure_ascii=False, indent=2)[:60000]}\n"
        "```"
    )


def _generate_with_deepseek(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com",
    )
    model = os.getenv("DEEPSEEK_MODEL") or "deepseek-v4-flash"
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是澜页 MarginMind 的阅读笔记生成器。你会看到内部上下文包，"
                    "但你的输出必须是用户可直接阅读的最终笔记，不能泄露内部上下文结构。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return response.choices[0].message.content or ""


def _generate_with_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "你是澜页 MarginMind 的阅读笔记生成器。只输出给用户看的最终笔记。",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def _generate_local(
    document: dict[str, Any],
    analysis: dict[str, Any],
    note_goal: str,
    reader_profile: dict[str, Any],
) -> str:
    title = document.get("title") or "未命名文档"
    lines = [
        f"# {title} - 澜页阅读笔记",
        "",
        f"阅读目标：{note_goal or '未填写'}",
        "",
        "## 阅读证据概况",
        f"- 本次有效视线样本：{analysis.get('sample_count', 0)}",
        f"- 本次提交页码：{', '.join(str(page) for page in analysis.get('read_scope', {}).get('read_pages', [])) or '暂无稳定阅读页'}",
        "- 主动标注是强证据；视线停留只是弱线索。证据不足时请以原文复核为准。",
        "",
        "## 主动标注与视线线索",
    ]

    any_focus = False
    for page in analysis.get("pages", []):
        focus = page.get("top_focus", [])
        if not focus:
            continue
        any_focus = True
        lines.append(f"### 第 {page.get('page_number')} 页")
        for item in focus[:5]:
            lines.append(f"- 系统观察到停留约 {item.get('seconds')} 秒：{item.get('text')}")

    if not any_focus:
        lines.append("- 暂未得到足够有效的视线线索。请结合主动标注和原文复核。")

    lines.extend(["", "## 可能需要回看"])
    any_skim = False
    for page in analysis.get("pages", []):
        skimmed = page.get("skimmed", [])
        if not skimmed:
            continue
        any_skim = True
        lines.append(f"### 第 {page.get('page_number')} 页")
        for item in skimmed[:4]:
            lines.append(f"- {item.get('text')}")
    if not any_skim:
        lines.append("- 暂无明显的一眼带过片段。")

    lines.extend(["", "## 主动标注"])
    any_selection = False
    for page in analysis.get("pages", []):
        for selection in page.get("selections", []):
            any_selection = True
            lines.append(f"- 第 {page.get('page_number')} 页：{selection.get('text')}")
    if not any_selection:
        lines.append("- 本次阅读没有额外主动标注。")

    lines.extend(
        [
            "",
            "## 建议",
            "- 对视线停留很久的内容，先写一句“我为什么在这里停住”，再整理定义或结论。",
            "- 对一眼带过但位于论证链条中的内容，建议快速回看，避免笔记只覆盖最显眼的句子。",
            "- 本笔记是阅读后的镜子，不是最终答案；保留一段自己的反驳、困惑或例子会更有价值。",
            "",
            "## 自测问题",
        ]
    )
    for page in document.get("pages", [])[:4]:
        text = " ".join(str(page.get("text") or "").split())[:160]
        if text:
            lines.append(f"- 第 {page.get('page_number')} 页：这页的核心问题是什么？请用一句自己的话回答。")

    return "\n".join(lines)


def _deepseek_provider_name() -> str:
    return f"deepseek:{os.getenv('DEEPSEEK_MODEL') or 'deepseek-v4-flash'}"


def _trim(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
