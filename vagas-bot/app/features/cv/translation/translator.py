from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm.client import get_llm

_LANG_LABEL = {
    "pt": "Portuguese (pt-BR)",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
}


def _system_prompt(target_lang: str) -> str:
    label = _LANG_LABEL[target_lang]
    return (
        f"You translate résumés into {label}. Output GitHub-flavored Markdown ONLY.\n"
        "Rules:\n"
        "- Preserve all factual content; do not invent experiences, dates, or skills.\n"
        "- Keep proper nouns (company names, schools, certifications, product names) as-is.\n"
        "- Use natural professional phrasing of the target language; do not transliterate.\n"
        f"- Format dates in the target language convention (e.g., en: 'Jan 2023 – Present').\n"
        "- Top-level header `# <Full Name>` if a name is detectable, otherwise omit.\n"
        "- Use `## Summary`, `## Experience`, `## Education`, `## Skills`, `## Languages`,\n"
        "  `## Projects`, `## Certifications` as appropriate, only when content exists.\n"
        "- Inside each section, use bullets (`-`) for items; bold company/role lines.\n"
        "- Do not add commentary, code fences, or anything outside the markdown body."
    )


async def translate_cv_to_markdown(cv_text: str, target_lang: str) -> str:
    if target_lang not in _LANG_LABEL:
        raise ValueError(f"unsupported target_lang: {target_lang}")
    llm = get_llm("SMART")
    messages = [
        SystemMessage(content=_system_prompt(target_lang)),
        HumanMessage(content=cv_text),
    ]
    last_err: Exception | None = None
    for _ in range(2):
        try:
            result = await llm.ainvoke(messages)
            content = result.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            text = str(content).strip()
            if text.startswith("```"):
                text = text.strip("`")
                if "\n" in text:
                    text = text.split("\n", 1)[1]
                text = text.rstrip("`").strip()
            return text
        except Exception as e:
            last_err = e
    raise RuntimeError(f"translation failed: {last_err!s}") from last_err
