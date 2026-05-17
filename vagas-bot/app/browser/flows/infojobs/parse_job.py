from dataclasses import dataclass

from playwright.async_api import BrowserContext

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


async def _safe_text(page, selector: str) -> str | None:
    el = await page.query_selector(selector)
    if el is None:
        return None
    txt = (await el.inner_text()).strip()
    return txt or None


async def parse_job_page(context: BrowserContext, *, url: str) -> VagaDetalhe:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await page.wait_for_selector(SELECTORS.job_title, timeout=15_000)
        await page.wait_for_timeout(2000)

        titulo = await _safe_text(page, SELECTORS.job_title) or "(sem título)"
        empresa = await _safe_text(page, SELECTORS.job_company)
        localidade = await _safe_text(page, SELECTORS.job_location)

        sections = await page.query_selector_all(SELECTORS.job_description_section)
        partes = []
        for el in sections:
            txt = (await el.inner_text()).strip()
            if txt:
                partes.append(txt)
        descricao = "\n\n".join(partes)

        if localidade:
            localidade = localidade.split("\n")[0].strip()[:160]

        return VagaDetalhe(
            url=url,
            gupy_external_id=None,
            titulo=titulo[:255],
            empresa=empresa[:160] if empresa else None,
            localidade=localidade,
            modalidade=None,
            descricao=descricao,
        )
    finally:
        await page.close()
