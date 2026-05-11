import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.features.sessao_gupy.models import SessaoGupy
from app.features.sessao_gupy.service import load_storage_state, save_storage_state


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SessaoGupy.__table__.create)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_save_then_load_roundtrip(session):
    state = {"cookies": [{"name": "s", "value": "v"}], "origins": []}
    await save_storage_state(session, json.dumps(state).encode(), rotulo="default")
    loaded = await load_storage_state(session, rotulo="default")
    assert json.loads(loaded.decode()) == state


async def test_load_returns_none_when_absent(session):
    loaded = await load_storage_state(session, rotulo="default")
    assert loaded is None


async def test_save_replaces_existing(session):
    await save_storage_state(session, b"first", rotulo="default")
    await save_storage_state(session, b"second", rotulo="default")
    loaded = await load_storage_state(session, rotulo="default")
    assert loaded == b"second"
    result = await session.execute(select(SessaoGupy))
    assert len(result.scalars().all()) == 1
