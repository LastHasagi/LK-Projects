import re
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page

from app.browser.flows.infojobs.selectors import SELECTORS
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class VagaDetalhe:
    url: str
    gupy_external_id: str | None
    titulo: str
    empresa: str | None
    localidade: str | None
    modalidade: str | None
    descricao: str


_COOKIE_BUTTONS = [
    "button:has-text('Aceitar')",
    "button:has-text('Concordo')",
    "button:has-text('OK')",
    "button[mode='primary']",
    "[id*='cookie'] button",
    "[class*='cookie'] button",
]
_URL_SLUG_RE = re.compile(r"/vaga-de-(?P<slug>.+?)(?:-em-(?P<city>[^_]+))?__(?P<id>\d+)\.aspx")
_TITLE_TAIL = re.compile(r"\s*[-|–]\s*infojobs.*$", re.IGNORECASE)


async def _dismiss_cookie_banner(page: Page) -> None:
    for sel in _COOKIE_BUTTONS:
        try:
            btn = await page.query_selector(sel)
            if btn is None or not await btn.is_visible():
                continue
            await btn.click(timeout=1500)
            await page.wait_for_timeout(500)
            return
        except Exception:
            continue


def _humanize(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split() if w)


def _parse_url_hints(url: str) -> tuple[str | None, str | None, str | None]:
    m = _URL_SLUG_RE.search(urlparse(url).path)
    if not m:
        return None, None, None
    titulo = _humanize(m.group("slug")) if m.group("slug") else None
    cidade = _humanize(m.group("city")) if m.group("city") else None
    return titulo, cidade, m.group("id")


async def parse_job_page(context: BrowserContext, *, url: str) -> VagaDetalhe:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await _dismiss_cookie_banner(page)
        await page.wait_for_timeout(2000)

        url_titulo, url_cidade, external_id = _parse_url_hints(url)

        doc_title = (await page.title() or "").strip()
        doc_title = _TITLE_TAIL.sub("", doc_title).strip()
        titulo = doc_title or url_titulo or "(sem título)"

        partes: list[str] = []
        sections = await page.query_selector_all(SELECTORS.job_description_section)
        for el in sections:
            txt = (await el.inner_text()).strip()
            if txt:
                partes.append(txt)
        if not partes:
            body = await page.eval_on_selector("body", "e => e.innerText")
            partes.append(body.strip()[:8000] if body else "")
        descricao = "\n\n".join(p for p in partes if p)

        return VagaDetalhe(
            url=url,
            gupy_external_id=external_id,
            titulo=titulo[:255],
            empresa=None,
            localidade=url_cidade,
            modalidade=None,
            descricao=descricao,
        )
    finally:
        await page.close()
