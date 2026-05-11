from unittest.mock import AsyncMock, patch

import httpx
import pytest
from asgi_lifespan import LifespanManager

from app.core.api import create_api


@pytest.mark.asyncio
async def test_healthz_ok():
    api = create_api()
    with patch("app.core.api.ping_db", new=AsyncMock(return_value=True)), \
         patch("app.core.api.ping_redis", new=AsyncMock(return_value=True)):
        async with LifespanManager(api):
            transport = httpx.ASGITransport(app=api)
            async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
                r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok", "redis": "ok"}


@pytest.mark.asyncio
async def test_healthz_degraded():
    api = create_api()
    with patch("app.core.api.ping_db", new=AsyncMock(return_value=False)), \
         patch("app.core.api.ping_redis", new=AsyncMock(return_value=True)):
        async with LifespanManager(api):
            transport = httpx.ASGITransport(app=api)
            async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
                r = await client.get("/healthz")
    assert r.status_code == 503
    body = r.json()
    assert body["db"] == "fail"
