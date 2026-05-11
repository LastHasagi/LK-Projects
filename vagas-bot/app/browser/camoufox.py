from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import BrowserContext


@asynccontextmanager
async def open_context(
    *,
    headless: bool = True,
    storage_state: dict | str | Path | None = None,
    locale: str = "pt-BR",
) -> AsyncIterator[BrowserContext]:
    async with AsyncCamoufox(
        headless=headless,
        locale=locale,
        humanize=True,
    ) as browser:
        context = await browser.new_context(storage_state=storage_state)
        try:
            yield context
        finally:
            await context.close()
