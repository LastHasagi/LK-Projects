from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.features.filtros.models import Filtro
from app.features.filtros.service import (
    criar_filtro,
    desativar_filtro,
    filtros_vencidos,
    listar_filtros,
    marcar_executado,
)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Filtro.__table__.create)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_criar_e_listar(session):
    f = await criar_filtro(
        session,
        nome="backend",
        query="python backend",
        localidade=None,
        modalidade="remoto",
        nivel="senior",
        intervalo_min=60,
    )
    assert f.id is not None
    assert f.ativo is True
    todos = await listar_filtros(session)
    assert len(todos) == 1


async def test_desativar(session):
    f = await criar_filtro(session, nome="x", query="x", intervalo_min=120)
    await desativar_filtro(session, f.id)
    todos = await listar_filtros(session, ativos=False)
    assert todos[0].ativo is False


async def test_filtros_vencidos(session):
    f1 = await criar_filtro(session, nome="a", query="x", intervalo_min=60)
    f2 = await criar_filtro(session, nome="b", query="y", intervalo_min=60)
    now = datetime.now(timezone.utc)
    await marcar_executado(session, f1.id, when=now - timedelta(minutes=30))
    await marcar_executado(session, f2.id, when=now - timedelta(minutes=120))
    devidos = await filtros_vencidos(session, now=now)
    assert {f.id for f in devidos} == {f2.id}


async def test_filtros_vencidos_inclui_nunca_executados(session):
    f = await criar_filtro(session, nome="z", query="z", intervalo_min=60)
    devidos = await filtros_vencidos(session, now=datetime.now(timezone.utc))
    assert f.id in {d.id for d in devidos}
