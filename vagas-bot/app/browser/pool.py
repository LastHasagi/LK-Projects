"""Long-lived Camoufox browser + per-ATS context pool.

One AsyncCamoufox process per worker. Each ATS gets its own BrowserContext
(isolated cookies/storage), created lazily on first acquisition and reused
for the rest of the worker's lifetime. Pages are created per job inside the
ATS context — concurrency comes from page parallelism, not browser cloning.
"""

import asyncio
from typing import Awaitable, Callable

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import Browser, BrowserContext

from app.core.logging import get_logger

log = get_logger(__name__)

StorageStateLoader = Callable[[], Awaitable[dict | None]]

_browser_cm: AsyncCamoufox | None = None
_browser: Browser | None = None
_browser_lock = asyncio.Lock()
_contexts: dict[str, BrowserContext] = {}
_context_locks: dict[str, asyncio.Lock] = {}


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
        _contexts.clear()
        _browser_cm = AsyncCamoufox(headless=True, locale="pt-BR", humanize=True)
        _browser = await _browser_cm.__aenter__()
        log.info("camoufox_launched")
    return _browser


async def get_context(
    ats: str,
    *,
    storage_state_loader: StorageStateLoader | None = None,
) -> BrowserContext:
    cached = _contexts.get(ats)
    if cached is not None:
        return cached
    lock = _context_locks.setdefault(ats, asyncio.Lock())
    async with lock:
        cached = _contexts.get(ats)
        if cached is not None:
            return cached
        browser = await _ensure_browser()
        storage_state = await storage_state_loader() if storage_state_loader else None
        context = await browser.new_context(storage_state=storage_state)
        _contexts[ats] = context
        log.info(
            "context_created",
            ats=ats,
            has_storage_state=storage_state is not None,
        )
        return context


async def invalidate_context(ats: str) -> None:
    """Drop the cached context for `ats`. Next get_context reloads storage."""
    ctx = _contexts.pop(ats, None)
    if ctx is None:
        return
    try:
        await ctx.close()
    except Exception as e:
        log.warning("context_close_failed", ats=ats, error=str(e))
    log.info("context_invalidated", ats=ats)


async def shutdown_browser() -> None:
    global _browser, _browser_cm
    for ats in list(_contexts.keys()):
        await invalidate_context(ats)
    if _browser_cm is not None:
        try:
            await _browser_cm.__aexit__(None, None, None)
        except Exception as e:
            log.warning("camoufox_exit_failed", error=str(e))
        _browser_cm = None
        _browser = None
        log.info("camoufox_shutdown")
