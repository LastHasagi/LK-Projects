import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.features.candidatura.models import Candidatura, CandidaturaStatus
from app.features.descoberta.models import Vaga  # noqa: F401 — registers vaga in Base.metadata
from app.features.candidatura.service import (
    cancelar,
    criar_candidatura,
    listar_em_andamento,
    marcar_aplicada,
    marcar_falha,
    marcar_pergunta_pendente,
    retomar_apos_resposta,
)

_DDL = [
    """
    CREATE TABLE vaga (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL DEFAULT 'stub'
    )
    """,
    """
    CREATE TABLE candidatura (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vaga_id INTEGER NOT NULL REFERENCES vaga(id),
        status VARCHAR(30) NOT NULL DEFAULT 'queued',
        tentativas INTEGER NOT NULL DEFAULT 0,
        ultimo_erro TEXT,
        screenshot_path VARCHAR(512),
        pergunta_pendente TEXT,
        pergunta_field_id VARCHAR(160),
        criada_em DATETIME DEFAULT CURRENT_TIMESTAMP,
        atualizada_em DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        for stmt in _DDL:
            await conn.execute(text(stmt))
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as s:
        yield s
    await engine.dispose()


async def test_criar_estado_inicial(session):
    c = await criar_candidatura(session, vaga_id=1)
    assert c.status == CandidaturaStatus.QUEUED.value
    assert c.tentativas == 0


async def test_marcar_pergunta_pendente(session):
    c = await criar_candidatura(session, vaga_id=1)
    await marcar_pergunta_pendente(session, c.id, pergunta="Pretensao?", field_id="f1")
    await session.refresh(c)
    assert c.status == CandidaturaStatus.PENDING_USER_INPUT.value
    assert c.pergunta_pendente == "Pretensao?"


async def test_retomar_limpa_pergunta(session):
    c = await criar_candidatura(session, vaga_id=1)
    await marcar_pergunta_pendente(session, c.id, pergunta="?", field_id="f1")
    await retomar_apos_resposta(session, c.id)
    await session.refresh(c)
    assert c.status == CandidaturaStatus.QUEUED.value
    assert c.pergunta_pendente is None


async def test_listar_em_andamento(session):
    c1 = await criar_candidatura(session, vaga_id=1)
    c2 = await criar_candidatura(session, vaga_id=2)
    await marcar_aplicada(session, c2.id, screenshot="/x.png")
    em_andamento = await listar_em_andamento(session)
    assert {c.id for c in em_andamento} == {c1.id}


async def test_marcar_falha_incrementa_tentativas(session):
    c = await criar_candidatura(session, vaga_id=1)
    await marcar_falha(session, c.id, erro="x")
    await session.refresh(c)
    assert c.tentativas == 1
    assert c.status == CandidaturaStatus.FAILED.value


async def test_cancelar(session):
    c = await criar_candidatura(session, vaga_id=1)
    await cancelar(session, c.id)
    await session.refresh(c)
    assert c.status == CandidaturaStatus.CANCELLED.value
