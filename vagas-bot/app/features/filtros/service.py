from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.filtros.models import Filtro


async def criar_filtro(
    session: AsyncSession,
    *,
    nome: str,
    query: str,
    localidade: str | None = None,
    modalidade: str | None = None,
    nivel: str | None = None,
    intervalo_min: int = 120,
    ats: str = "gupy",
) -> Filtro:
    f = Filtro(
        nome=nome,
        query=query,
        localidade=localidade,
        modalidade=modalidade,
        nivel=nivel,
        intervalo_min=intervalo_min,
        ativo=True,
        ats=ats,
    )
    session.add(f)
    await session.commit()
    await session.refresh(f)
    return f


async def listar_filtros(
    session: AsyncSession, *, ativos: bool | None = True
) -> list[Filtro]:
    stmt = select(Filtro).order_by(Filtro.criada_em.desc())
    if ativos is not None:
        stmt = stmt.where(Filtro.ativo.is_(ativos))
    return list((await session.execute(stmt)).scalars())


async def desativar_filtro(session: AsyncSession, filtro_id: int) -> None:
    await session.execute(
        update(Filtro).where(Filtro.id == filtro_id).values(ativo=False)
    )
    await session.commit()


async def atualizar_filtro(
    session: AsyncSession,
    filtro_id: int,
    *,
    nome: str | None = None,
    query: str | None = None,
    localidade: str | None = None,
    modalidade: str | None = None,
    nivel: str | None = None,
    intervalo_min: int | None = None,
    ativo: bool | None = None,
    ats: str | None = None,
) -> Filtro | None:
    valores: dict = {}
    if nome is not None:
        valores["nome"] = nome
    if query is not None:
        valores["query"] = query
    if localidade is not None:
        valores["localidade"] = localidade
    if modalidade is not None:
        valores["modalidade"] = modalidade
    if nivel is not None:
        valores["nivel"] = nivel
    if intervalo_min is not None:
        valores["intervalo_min"] = intervalo_min
    if ativo is not None:
        valores["ativo"] = ativo
    if ats is not None:
        valores["ats"] = ats
    if valores:
        await session.execute(
            update(Filtro).where(Filtro.id == filtro_id).values(**valores)
        )
        await session.commit()
    return await session.get(Filtro, filtro_id)


async def marcar_executado(
    session: AsyncSession, filtro_id: int, *, when: datetime | None = None
) -> None:
    quando = when or datetime.now(timezone.utc)
    await session.execute(
        update(Filtro).where(Filtro.id == filtro_id).values(ultima_busca_em=quando)
    )
    await session.commit()


async def filtros_vencidos(
    session: AsyncSession, *, now: datetime
) -> list[Filtro]:
    stmt = select(Filtro).where(Filtro.ativo.is_(True))
    rows = list((await session.execute(stmt)).scalars())
    devidos: list[Filtro] = []
    for f in rows:
        if f.ultima_busca_em is None:
            devidos.append(f)
            continue
        delta_min = (now - f.ultima_busca_em).total_seconds() / 60
        if delta_min >= f.intervalo_min:
            devidos.append(f)
    return devidos
