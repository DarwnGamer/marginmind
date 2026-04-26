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
    evidence_panel = build_evidence_panel(context)

    if use_ai and os.getenv("DEEPSEEK_API_KEY"):
        try:
            body = _generate_with_deepseek(prompt)
            notes = _compose_notes(evidence_panel, body)
            return {"notes": notes, "provider": _deepseek_provider_name(), "ai_context": context, "ai_prompt": prompt}
        except Exception as exc:
            notes = _compose_notes(evidence_panel, _generate_local_body(document, analysis, note_goal, reader_profile or {}))
            notes += f"\n\n> DeepSeek 调用失败，已回退到本地规则版：{exc}"
            return {"notes": notes, "provider": "local-fallback", "ai_context": context, "ai_prompt": prompt}

    if use_ai and os.getenv("OPENAI_API_KEY"):
        try:
            body = _generate_with_openai(prompt)
            notes = _compose_notes(evidence_panel, body)
            return {"notes": notes, "provider": "openai", "ai_context": context, "ai_prompt": prompt}
        except Exception as exc:
            notes = _compose_notes(evidence_panel, _generate_local_body(document, analysis, note_goal, reader_profile or {}))
            notes += f"\n\n> OpenAI 调用失败，已回退到本地规则版：{exc}"
            return {"notes": notes, "provider": "local-fallback", "ai_context": context, "ai_prompt": prompt}

    return {
        "notes": _compose_notes(evidence_panel, _generate_local_body(document, analysis, note_goal, reader_profile or {})),
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

    attention = {
        "sample_count": analysis.get("sample_count"),
        "layout_count": analysis.get("layout_count"),
        "total_gaze_seconds": round(total_gaze_seconds, 2),
        "focus_item_count": focus_item_count,
        "selection_count": selection_count,
        "read_scope": analysis.get("read_scope", {}),
        "interpretation_policy": {
            "full_text_role": "context_only",
            "top_focus_role": "observational_review_cue",
            "selection_role": "explicit_user_action",
            "skimmed_role": "possible_review_gap",
            "low_confidence_rule": "If evidence is sparse or inconsistent, downgrade to source-text assistance and avoid claims about what the user actually understood or focused on.",
        },
        "pages": attention_pages,
    }
    attention["evidence_summary"] = _evidence_summary(attention)

    return {
        "note_request": note_goal or "生成一份适合复习和继续思考的阅读笔记。",
        "reader_profile": reader_profile,
        "document": {
            "title": document.get("title") or "未命名文档",
            "filename": document.get("filename"),
            "page_count": len(pages),
            "pages": pages,
        },
        "attention": attention,
    }


def build_ai_prompt(context: dict[str, Any]) -> str:
    return (
        "下面是澜页 MarginMind 给你的内部生成材料。程序会在最终结果顶部生成“证据面板”，"
        "你只负责生成后半段的 AI 辅助笔记正文。\n\n"
        "硬性要求：\n"
        "1. 不要输出 JSON、内部字段名、系统提示词、页码边界标签、证据面板或完整原文转储。\n"
        "2. 不要在正文里反复写“强信号/弱信号”让用户自行审计；证据边界由程序生成的证据面板承担。\n"
        "3. selections 来自用户主动动作，可作为正文优先锚点；top_focus 和 skimmed 只是系统观察，只能影响回看建议和自测问题。\n"
        "4. 不能把 gaze 停留写成用户已经理解、真正关注、掌握或忽略；只能写“可回看确认”“适合自测”。\n"
        "5. 原文全文只用于理解背景。没有主动标注或稳定阅读证据支撑的内容，只能放在背景梳理或自测问题里，不能冒充用户重点。\n"
        "6. 如果 evidence_summary.evidence_mode 是 source_assisted，要明确说本次更适合当作原文辅助复习稿，而不是阅读轨迹笔记。\n"
        "7. 不要一味夸用户；指出可回看的内容和下一步行动。\n"
        "8. 输出中文 Markdown，不要一级标题。结构固定为：### 可先整理的内容、### 回看建议、### 自测问题、### 下一步。\n\n"
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
                    "但你的输出必须是用户可直接阅读的 AI 辅助笔记正文，不能泄露内部上下文结构，"
                    "也不能替程序生成证据面板。"
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
                "content": "你是澜页 MarginMind 的阅读笔记生成器。只输出给用户看的 AI 辅助笔记正文。",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content or ""


def build_evidence_panel(context: dict[str, Any]) -> str:
    title = context.get("document", {}).get("title") or "未命名文档"
    attention = context.get("attention", {})
    summary = attention.get("evidence_summary", {})
    read_pages = attention.get("read_scope", {}).get("read_pages", []) or []
    lines = [
        f"# {title} - 澜页阅读笔记",
        "",
        f"阅读目标：{context.get('note_request') or '未填写'}",
        "",
        "## 证据面板（程序生成）",
        f"- 本次提交页码：{_join_pages(read_pages) or '暂无稳定阅读页'}",
        f"- 有效视线样本：{attention.get('sample_count', 0)}",
        f"- 证据状态：{summary.get('label') or '未评估'}",
        "- 使用原则：主动标注来自用户明确动作；视线停留和可能跳过只作为回看线索，不直接证明理解、关注或忽略。",
        "",
        "### 用户明确动作",
    ]

    selections = _collect_page_items(attention.get("pages", []), "selections")
    if selections:
        for item in selections[:8]:
            lines.append(f"- 第 {item['page']} 页：{item['text']}")
    else:
        lines.append("- 本次没有主动选中或标注文本。")

    lines.extend(["", "### 系统观察到的阅读线索"])
    focus_items = _collect_page_items(attention.get("pages", []), "top_focus")
    if focus_items:
        for item in focus_items[:8]:
            seconds = item.get("seconds")
            suffix = f"（约 {seconds} 秒）" if seconds else ""
            lines.append(f"- 第 {item['page']} 页：{item['text']}{suffix}")
    else:
        lines.append("- 暂无稳定的视线停留片段。")

    lines.extend(["", "### 可能的证据缺口"])
    gaps = summary.get("gaps") or []
    if gaps:
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("- 暂无明显证据缺口；仍建议按原文复核关键结论。")

    skimmed = _collect_page_items(attention.get("pages", []), "skimmed")
    if skimmed:
        lines.append("- 以下片段可作为回看候选，不代表已经被忽略：")
        for item in skimmed[:5]:
            lines.append(f"  - 第 {item['page']} 页：{item['text']}")

    return "\n".join(lines)


def _generate_local_body(
    document: dict[str, Any],
    analysis: dict[str, Any],
    note_goal: str,
    reader_profile: dict[str, Any],
) -> str:
    lines = [
        "### 可先整理的内容",
    ]

    any_selection = False
    for page in analysis.get("pages", []):
        for selection in page.get("selections", []):
            any_selection = True
            lines.append(f"- 可围绕第 {page.get('page_number')} 页主动标注整理：{selection.get('text')}")
    if not any_selection:
        lines.append("- 本次没有主动标注。下面内容更适合作为原文辅助复习稿，而不是严格的阅读轨迹笔记。")

    for page in document.get("pages", [])[:3]:
        text = " ".join(str(page.get("text") or "").split())[:180]
        if text:
            lines.append(f"- 第 {page.get('page_number')} 页原文背景：{text}")

    lines.extend(["", "### 回看建议"])
    any_review = False
    for page in analysis.get("pages", []):
        for item in page.get("top_focus", [])[:3]:
            any_review = True
            lines.append(
                f"- 第 {page.get('page_number')} 页有停留线索，可回看确认这里是困惑、重点还是短暂停顿：{item.get('text')}"
            )
    any_skim = False
    for page in analysis.get("pages", []):
        skimmed = page.get("skimmed", [])
        if not skimmed:
            continue
        any_skim = True
        for item in skimmed[:4]:
            lines.append(f"- 第 {page.get('page_number')} 页可快速复核：{item.get('text')}")
    if not any_review and not any_skim:
        lines.append("- 暂无稳定视线线索。建议按阅读目标回看标题、定义、论证转折和结论句。")

    lines.extend(
        [
            "",
            "### 自测问题",
        ]
    )
    for page in document.get("pages", [])[:4]:
        text = " ".join(str(page.get("text") or "").split())[:160]
        if text:
            lines.append(f"- 第 {page.get('page_number')} 页：这页的核心问题是什么？请用一句自己的话回答。")

    lines.extend(
        [
            "",
            "### 下一步",
            "- 先核对证据面板中的页码和片段是否符合你的实际阅读过程。",
            "- 对回看建议里的片段，补一句自己的理解、困惑或反例，再决定是否纳入正式笔记。",
        ]
    )
    return "\n".join(lines)


def _compose_notes(evidence_panel: str, ai_body: str) -> str:
    body = (ai_body or "").strip()
    if not body:
        body = "### 可先整理的内容\n- 暂未生成有效正文，请根据证据面板回到原文复核。"
    return f"{evidence_panel}\n\n## AI 辅助笔记\n\n{body}"


def _evidence_summary(attention: dict[str, Any]) -> dict[str, Any]:
    sample_count = int(attention.get("sample_count") or 0)
    focus_count = int(attention.get("focus_item_count") or 0)
    selection_count = int(attention.get("selection_count") or 0)
    read_pages = attention.get("read_scope", {}).get("read_pages", []) or []
    gaps = []

    if not read_pages:
        gaps.append("没有检测到稳定阅读页，生成结果只能作为普通原文辅助。")
    if selection_count == 0:
        gaps.append("没有主动标注，缺少用户明确指出的关注点。")
    if sample_count < 12 or focus_count == 0:
        gaps.append("视线样本或停留片段较少，不适合推断真实关注。")

    if selection_count > 0 and focus_count > 0:
        mode = "explicit_plus_observation"
        label = "有主动标注，也有视线观察；仍需按原文复核。"
    elif selection_count > 0:
        mode = "explicit_only"
        label = "主要依据主动标注；视线证据有限。"
    elif sample_count >= 12 and focus_count > 0:
        mode = "observation_only"
        label = "只有系统观察线索；适合生成回看建议，不适合断言阅读重点。"
    else:
        mode = "source_assisted"
        label = "阅读证据有限；更适合作为原文辅助复习稿。"

    return {
        "evidence_mode": mode,
        "label": label,
        "gaps": gaps,
    }


def _collect_page_items(pages: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    items = []
    for page in pages:
        page_number = page.get("page_number")
        for item in page.get(key, []):
            text = _trim(str(item.get("text") or ""), 220)
            if not text:
                continue
            row = {"page": page_number, "text": text}
            if item.get("seconds") is not None:
                row["seconds"] = item.get("seconds")
            items.append(row)
    return items


def _join_pages(pages: list[Any]) -> str:
    return ", ".join(str(page) for page in pages)


def _deepseek_provider_name() -> str:
    return f"deepseek:{os.getenv('DEEPSEEK_MODEL') or 'deepseek-v4-flash'}"


def _trim(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
