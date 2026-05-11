from dataclasses import dataclass
from urllib.parse import quote_plus

from playwright.async_api import BrowserContext

from app.browser.selectors import SELECTORS
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class VagaPreview:
    url: str
    titulo: str
    empresa: str | None
    localidade: str | None
    modalidade: str | None


async def search_listings(
    context: BrowserContext, *, query: str, max_items: int = 30
) -> list[VagaPreview]:
    url = SELECTORS.search_url.format(query=quote_plus(query))
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await page.wait_for_selector(SELECTORS.listing_item, timeout=15_000)
        items = await page.query_selector_all(SELECTORS.listing_item)
        log.info("listings_found", count=len(items), query=query)

        results: list[VagaPreview] = []
        seen: set[str] = set()
        for el in items[:max_items]:
            href = await el.get_attribute("href")
            if not href:
                continue
            full_url = href if href.startswith("http") else f"https://portal.gupy.io{href}"
            if full_url in seen:
                continue
            seen.add(full_url)
            titulo = (await el.inner_text()).strip().split("\n")[0][:200] or "(sem título)"
            results.append(
                VagaPreview(
                    url=full_url,
                    titulo=titulo,
                    empresa=None,
                    localidade=None,
                    modalidade=None,
                )
            )
        return results
    finally:
        await page.close()
