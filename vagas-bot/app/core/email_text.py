import re

_EMAIL_RE = re.compile(
    r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b",
)


def extract_emails(text: str) -> list[str]:
    """Extrai endereços de e-mail de um texto, sem duplicatas, preservando a ordem.

    Args:
        text: Texto livre (ex.: post do LinkedIn).

    Returns:
        Lista de e-mails em minúsculas.
    """
    seen: set[str] = set()
    out: list[str] = []
    for m in _EMAIL_RE.finditer(text or ""):
        addr = m.group(0).lower()
        if addr not in seen:
            seen.add(addr)
            out.append(addr)
    return out
