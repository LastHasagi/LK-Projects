import re
from dataclasses import dataclass
from urllib.parse import urlparse

from playwright.async_api import BrowserContext

from app.browser.selectors import SELECTORS
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


def _extract_external_id(url: str) -> str | None:
    path = urlparse(url).path.strip("/")
    parts = [p for p in path.split("/") if p]
    return parts[-1] if parts else None


def _empresa_from_url(url: str) -> str | None:
    host = urlparse(url).hostname or ""
    sub = host.split(".")[0] if "." in host else None
    if not sub or sub in {"portal", "www"}:
        return None
    return sub


_LOCAL_RE = re.compile(r"Local de trabalho:\s*([^\n]+?)\s*(?:\n|$)", re.IGNORECASE)
_MOD_RE = re.compile(r"Modelo de trabalho:\s*([^\n]+?)\s*(?:\n|$)", re.IGNORECASE)


async def parse_job_page(context: BrowserContext, *, url: str) -> VagaDetalhe:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await page.wait_for_selector(SELECTORS.job_title, timeout=15_000)
        await page.wait_for_timeout(2000)

        title_el = await page.query_selector(SELECTORS.job_title)
        titulo = (await title_el.inner_text()).strip() if title_el else "(sem título)"

        sections = await page.query_selector_all(SELECTORS.job_description_section)
        partes = []
        for el in sections:
            txt = (await el.inner_text()).strip()
            if txt:
                partes.append(txt)
        descricao = "\n\n".join(partes)

        body_text = await page.eval_on_selector("body", "e => e.innerText")
        local_match = _LOCAL_RE.search(body_text)
        mod_match = _MOD_RE.search(body_text)
        localidade = local_match.group(1).strip() if local_match else None
        modalidade = mod_match.group(1).strip() if mod_match else None

        if localidade:
            localidade = localidade.split("\n")[0].strip()[:160]
        if modalidade:
            modalidade = modalidade.split("\n")[0].strip()[:30]

        return VagaDetalhe(
            url=url,
            gupy_external_id=_extract_external_id(url),
            titulo=titulo,
            empresa=_empresa_from_url(url),
            localidade=localidade,
            modalidade=modalidade,
            descricao=descricao,
        )
    finally:
        await page.close()
