from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.candidatura.models import Candidatura, CandidaturaStatus


async def criar_candidatura(session: AsyncSession, *, vaga_id: int) -> Candidatura:
    c = Candidatura(vaga_id=vaga_id, status=CandidaturaStatus.QUEUED.value)
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c


async def get_candidatura(session: AsyncSession, candidatura_id: int) -> Candidatura | None:
    return await session.get(Candidatura, candidatura_id)


async def marcar_aplicando(session: AsyncSession, candidatura_id: int) -> None:
    await session.execute(
        update(Candidatura)
        .where(Candidatura.id == candidatura_id)
        .values(status=CandidaturaStatus.APPLYING.value, tentativas=Candidatura.tentativas + 1)
    )
    await session.commit()


async def marcar_pergunta_pendente(
    session: AsyncSession,
    candidatura_id: int,
    *,
    pergunta: str,
    field_id: str | None = None,
    screenshot: str | None = None,
) -> None:
    values = {
        "status": CandidaturaStatus.PENDING_USER_INPUT.value,
        "pergunta_pendente": pergunta,
        "pergunta_field_id": field_id,
    }
    if screenshot:
        values["screenshot_path"] = screenshot
    await session.execute(
        update(Candidatura).where(Candidatura.id == candidatura_id).values(**values)
    )
    await session.commit()


async def retomar_apos_resposta(session: AsyncSession, candidatura_id: int) -> None:
    await session.execute(
        update(Candidatura)
        .where(Candidatura.id == candidatura_id)
        .values(
            status=CandidaturaStatus.QUEUED.value,
            pergunta_pendente=None,
            pergunta_field_id=None,
        )
    )
    await session.commit()


async def marcar_aplicada(
    session: AsyncSession, candidatura_id: int, *, screenshot: str | None = None
) -> None:
    await session.execute(
        update(Candidatura)
        .where(Candidatura.id == candidatura_id)
        .values(status=CandidaturaStatus.APPLIED.value, screenshot_path=screenshot)
    )
    await session.commit()


async def marcar_falha(
    session: AsyncSession,
    candidatura_id: int,
    *,
    erro: str,
    screenshot: str | None = None,
) -> None:
    await session.execute(
        update(Candidatura)
        .where(Candidatura.id == candidatura_id)
        .values(
            status=CandidaturaStatus.FAILED.value,
            ultimo_erro=erro[:2000],
            tentativas=Candidatura.tentativas + 1,
            screenshot_path=screenshot,
        )
    )
    await session.commit()


async def cancelar(session: AsyncSession, candidatura_id: int) -> None:
    await session.execute(
        update(Candidatura)
        .where(Candidatura.id == candidatura_id)
        .values(status=CandidaturaStatus.CANCELLED.value)
    )
    await session.commit()


async def listar_em_andamento(session: AsyncSession) -> list[Candidatura]:
    stmt = select(Candidatura).where(
        Candidatura.status.in_([
            CandidaturaStatus.QUEUED.value,
            CandidaturaStatus.APPLYING.value,
            CandidaturaStatus.PENDING_USER_INPUT.value,
        ])
    ).order_by(Candidatura.criada_em.desc())
    return list((await session.execute(stmt)).scalars())


async def candidatura_pelo_pergunta_pendente(
    session: AsyncSession,
) -> Candidatura | None:
    stmt = (
        select(Candidatura)
        .where(Candidatura.status == CandidaturaStatus.PENDING_USER_INPUT.value)
        .order_by(Candidatura.atualizada_em.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def contar_aplicadas_hoje(session: AsyncSession) -> int:
    hoje = datetime.now(timezone.utc).date()
    stmt = select(func.count()).select_from(Candidatura).where(
        Candidatura.status == CandidaturaStatus.APPLIED.value,
        func.date(Candidatura.atualizada_em) == hoje,
    )
    return int((await session.execute(stmt)).scalar_one())
