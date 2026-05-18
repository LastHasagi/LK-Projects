from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from playwright.async_api import BrowserContext

from app.browser.flows.infojobs.selectors import SELECTORS
from app.core.logging import get_logger

log = get_logger(__name__)

_DEBUG_DIR = Path("/app/data/screenshots")


@dataclass
class VagaPreview:
    url: str
    titulo: str
    empresa: str | None
    localidade: str | None
    modalidade: str | None


_COOKIE_BUTTONS = [
    "button:has-text('Aceitar')",
    "button:has-text('Concordo')",
    "button:has-text('OK')",
    "button[mode='primary']",
    "[id*='cookie'] button",
    "[class*='cookie'] button",
]


async def _dismiss_cookie_banner(page) -> None:
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


async def search_listings(
    context: BrowserContext, *, query: str, max_items: int = 30
) -> list[VagaPreview]:
    url = SELECTORS.search_url.format(query=quote_plus(query))
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await _dismiss_cookie_banner(page)
        try:
            await page.wait_for_selector(SELECTORS.listing_item, timeout=15_000)
        except Exception as e:
            try:
                _DEBUG_DIR.mkdir(parents=True, exist_ok=True)
                slug = "".join(c if c.isalnum() else "_" for c in query)[:40]
                shot = _DEBUG_DIR / f"infojobs_search_timeout_{slug}.png"
                await page.screenshot(path=str(shot), full_page=True)
                body = await page.content()
                log.error(
                    "infojobs_search_selector_timeout",
                    query=query,
                    landed_url=page.url,
                    landed_title=await page.title(),
                    body_len=len(body),
                    body_snippet=body[:500],
                    screenshot=str(shot),
                )
            except Exception as diag_err:
                log.warning("infojobs_search_diag_failed", error=str(diag_err))
            raise e
        items = await page.query_selector_all(SELECTORS.listing_item)
        log.info("infojobs_listings_found", count=len(items), query=query)

        results: list[VagaPreview] = []
        seen: set[str] = set()
        for el in items[:max_items]:
            href = await el.get_attribute("href")
            if not href:
                continue
            full_url = (
                href if href.startswith("http")
                else f"https://www.infojobs.com.br{href}"
            )
            if full_url in seen:
                continue
            seen.add(full_url)
            text = (await el.inner_text()).strip()
            titulo = text.split("\n")[0][:200] if text else "(sem título)"
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
