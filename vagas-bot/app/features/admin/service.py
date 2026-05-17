from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session_maker
from app.core.redis import get_redis
from app.features.candidatura.models import Candidatura, CandidaturaStatus, Evento
from app.features.cv.models import CV
from app.features.descoberta.models import Vaga
from app.features.filtros.models import Filtro
from app.features.sessao_gupy.models import SessaoGupy

PAUSE_KEY = "scrape:paused"


async def coletar_metricas(session: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    horizonte_24h = now - timedelta(hours=24)
    horizonte_7d = now - timedelta(days=7)

    total_vagas = (await session.execute(select(func.count()).select_from(Vaga))).scalar_one()
    vagas_24h = (
        await session.execute(
            select(func.count()).select_from(Vaga).where(Vaga.criada_em >= horizonte_24h)
        )
    ).scalar_one()

    cand_por_status = {}
    for status in CandidaturaStatus:
        c = (
            await session.execute(
                select(func.count())
                .select_from(Candidatura)
                .where(Candidatura.status == status.value)
            )
        ).scalar_one()
        cand_por_status[status.value] = c

    aplicadas_24h = (
        await session.execute(
            select(func.count())
            .select_from(Candidatura)
            .where(
                Candidatura.status == CandidaturaStatus.APPLIED.value,
                Candidatura.atualizada_em >= horizonte_24h,
            )
        )
    ).scalar_one()
    aplicadas_7d = (
        await session.execute(
            select(func.count())
            .select_from(Candidatura)
            .where(
                Candidatura.status == CandidaturaStatus.APPLIED.value,
                Candidatura.atualizada_em >= horizonte_7d,
            )
        )
    ).scalar_one()

    filtros_ativos = (
        await session.execute(
            select(func.count()).select_from(Filtro).where(Filtro.ativo.is_(True))
        )
    ).scalar_one()

    return {
        "vagas_total": total_vagas,
        "vagas_24h": vagas_24h,
        "candidaturas": cand_por_status,
        "aplicadas_24h": aplicadas_24h,
        "aplicadas_7d": aplicadas_7d,
        "filtros_ativos": filtros_ativos,
    }


async def coletar_health() -> dict:
    out = {}
    redis = get_redis()
    try:
        await redis.ping()
        out["redis"] = "ok"
        try:
            paused = await redis.get(PAUSE_KEY)
            out["scrape"] = "paused" if paused else "running"
        finally:
            pass
    except Exception as e:
        out["redis"] = f"fail: {e}"
        out["scrape"] = "?"
    try:
        await redis.aclose()
    except Exception:
        pass

    maker = get_session_maker()
    async with maker() as session:
        try:
            await session.execute(select(1))
            out["db"] = "ok"
        except Exception as e:
            out["db"] = f"fail: {e}"

        cv = (
            await session.execute(select(CV).where(CV.ativo.is_(True)))
        ).scalar_one_or_none()
        out["cv_ativo"] = "sim" if cv else "nao"

        sessao = (
            await session.execute(select(SessaoGupy).limit(1))
        ).scalar_one_or_none()
        out["sessao_gupy"] = "sim" if sessao else "nao"

        ultimo_filtro = (
            await session.execute(
                select(Filtro.ultima_busca_em)
                .where(Filtro.ultima_busca_em.isnot(None))
                .order_by(Filtro.ultima_busca_em.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        out["ultimo_scrape"] = (
            ultimo_filtro.strftime("%Y-%m-%d %H:%M") if ultimo_filtro else "nunca"
        )
    return out


async def listar_eventos_erro(session: AsyncSession, limit: int = 10) -> list[Evento]:
    stmt = (
        select(Evento)
        .where(Evento.tipo.in_(["erro", "scrape_failed", "apply_failed"]))
        .order_by(Evento.criado_em.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars())


async def set_pause_scrape(paused: bool) -> None:
    redis = get_redis()
    try:
        if paused:
            await redis.set(PAUSE_KEY, "1")
        else:
            await redis.delete(PAUSE_KEY)
    finally:
        await redis.aclose()


async def is_pause_scrape() -> bool:
    redis = get_redis()
    try:
        val = await redis.get(PAUSE_KEY)
        return val is not None
    finally:
        await redis.aclose()


async def limpar_fila() -> int:
    redis = get_redis()
    try:
        keys = await redis.keys("arq:*")
        if not keys:
            return 0
        return int(await redis.delete(*keys))
    finally:
        await redis.aclose()


async def resumo_filtros(session: AsyncSession) -> list[dict]:
    from app.features.candidatura.models import Candidatura

    stmt = (
        select(
            Filtro.id,
            Filtro.nome,
            Filtro.ativo,
            func.count(Vaga.id).label("vagas_total"),
            func.count(Candidatura.id).label("vagas_candidatadas"),
        )
        .select_from(Filtro)
        .outerjoin(Vaga, Vaga.filtro_id == Filtro.id)
        .outerjoin(Candidatura, Candidatura.vaga_id == Vaga.id)
        .where(Filtro.ativo.is_(True))
        .group_by(Filtro.id, Filtro.nome, Filtro.ativo)
        .order_by(Filtro.id)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": r.id,
            "nome": r.nome,
            "ativo": r.ativo,
            "pendentes": r.vagas_total - r.vagas_candidatadas,
            "total": r.vagas_total,
        }
        for r in rows
    ]


async def limpar_vagas_pendentes_do_filtro(
    session: AsyncSession, filtro_id: int
) -> int:
    from sqlalchemy import delete
    from app.features.candidatura.models import Candidatura
    from app.features.matching.models import MatchResult

    candidatada_subq = select(Candidatura.vaga_id).where(
        Candidatura.vaga_id == Vaga.id
    )
    pendentes_stmt = select(Vaga.id).where(
        Vaga.filtro_id == filtro_id,
        ~candidatada_subq.exists(),
    )
    pendentes_ids = list((await session.execute(pendentes_stmt)).scalars())
    if not pendentes_ids:
        return 0
    await session.execute(
        delete(MatchResult).where(MatchResult.vaga_id.in_(pendentes_ids))
    )
    await session.execute(delete(Vaga).where(Vaga.id.in_(pendentes_ids)))
    await session.commit()
    return len(pendentes_ids)
