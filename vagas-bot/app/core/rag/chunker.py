from pathlib import Path

import fitz


CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def parse_pdf(path: str | Path) -> str:
    doc = fitz.open(str(path))
    try:
        parts = [page.get_text("text") for page in doc]
        return "\n".join(parts).strip()
    finally:
        doc.close()


def chunk_text(text: str, max_tokens: int = 400, overlap_tokens: int = 50) -> list[str]:
    if not text:
        return []
    max_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            space = text.rfind(" ", start, end)
            if space > start + max_chars // 2:
                end = space
        chunks.append(text[start:end].strip())
        if end >= n:
            break
        start = max(end - overlap_chars, start + 1)
    return [c for c in chunks if c]
