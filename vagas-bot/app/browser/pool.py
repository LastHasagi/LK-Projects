"""Long-lived Camoufox browser + per-job BrowserContext.

One AsyncCamoufox process per worker, shared by all jobs. Each job opens
its own BrowserContext via `session(ats)` (isolated cookies/storage) and
closes it on exit. Contexts run in parallel inside the single browser —
this avoids the page-level contention observed when multiple jobs share a
single Context under Camoufox's humanize mode.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, BrowserContext

from app.core.logging import get_logger

log = get_logger(__name__)

StorageStateLoader = Callable[[], Awaitable[dict | None]]

_browser_cm: AsyncCamoufox | None = None
_browser: Browser | None = None
_browser_lock = asyncio.Lock()
_session_semaphore = asyncio.Semaphore(1)


async def _ensure_browser() -> Browser:
    global _browser_cm, _browser
    if _browser is not None and _browser.is_connected():
        return _browser
    async with _browser_lock:
        if _browser is not None and _browser.is_connected():
            return _browser
        if _browser_cm is not None:
            try:
                await _browser_cm.__aexit__(None, None, None)
            except Exception as e:
                log.warning("camoufox_prev_exit_failed", error=str(e))
        _browser_cm = AsyncCamoufox(headless=True, locale="pt-BR", humanize=True)
        _browser = await _browser_cm.__aenter__()
        log.info("camoufox_launched")
    return _browser


@asynccontextmanager
async def session(
    ats: str,
    *,
    storage_state_loader: StorageStateLoader | None = None,
):
    """Yield a fresh BrowserContext for the duration of a job.

    The context is closed on exit but the underlying browser keeps running.
    Browser sessions are serialized via a semaphore — Camoufox's humanize
    mode behaves badly with concurrent contexts in the same process.
    """
    async with _session_semaphore:
        browser = await _ensure_browser()
        storage_state = await storage_state_loader() if storage_state_loader else None
        context: BrowserContext = await browser.new_context(storage_state=storage_state)
        log.debug(
            "context_opened",
            ats=ats,
            has_storage_state=storage_state is not None,
        )
        try:
            yield context
        finally:
            try:
                await context.close()
            except Exception as e:
                log.warning("context_close_failed", ats=ats, error=str(e))


async def shutdown_browser() -> None:
    global _browser, _browser_cm
    if _browser_cm is not None:
        try:
            await _browser_cm.__aexit__(None, None, None)
        except Exception as e:
            log.warning("camoufox_exit_failed", error=str(e))
        _browser_cm = None
        _browser = None
        log.info("camoufox_shutdown")
