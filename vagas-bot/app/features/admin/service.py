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
