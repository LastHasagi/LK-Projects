from datetime import datetime, timezone

from arq.connections import ArqRedis, create_pool

from app.browser.pool import get_context
from app.browser.flows.parse_job import parse_job_page
from app.browser.flows.search import VagaPreview, search_listings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.features.descoberta.service import VagaCandidata, persistir_vaga, vaga_por_url
from app.features.filtros.models import Filtro
from app.features.filtros.service import filtros_vencidos, marcar_executado

log = get_logger(__name__)


async def scrape_all_due(ctx: dict) -> int:
    from app.features.admin.service import is_pause_scrape
    if await is_pause_scrape():
        log.info("scrape_all_due_paused")
        return 0
    maker = get_session_maker()
    async with maker() as session:
        devidos = await filtros_vencidos(session, now=datetime.now(timezone.utc))
    if not devidos:
        return 0
    log.info("scrape_all_due_dispatching", count=len(devidos))
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        for f in devidos:
            await pool.enqueue_job("scrape_search", f.id)
    finally:
        await pool.close()
    return len(devidos)


async def scrape_search(ctx: dict, filtro_id: int) -> int:
    maker = get_session_maker()
    async with maker() as session:
        filtro = await session.get(Filtro, filtro_id)
    if filtro is None or not filtro.ativo:
        log.warning("scrape_search_skipped", filtro_id=filtro_id)
        return 0

    log.info("scrape_search_started", filtro_id=filtro_id, query=filtro.query)
    context = await get_context("gupy")
    previews: list[VagaPreview] = []
    try:
        previews = await search_listings(context, query=filtro.query)
    except Exception as e:
        log.error("scrape_search_failed", filtro_id=filtro_id, error=str(e))

    novas = 0
    async with maker() as session:
        for preview in previews:
            if await vaga_por_url(session, preview.url) is not None:
                continue
            try:
                detalhe = await parse_job_page(context, url=preview.url)
            except Exception as e:
                log.warning("parse_job_failed", url=preview.url, error=str(e))
                detalhe = None
            candidata = VagaCandidata(
                url=preview.url,
                titulo=detalhe.titulo if detalhe else preview.titulo,
                empresa=detalhe.empresa if detalhe else preview.empresa,
                localidade=detalhe.localidade if detalhe else preview.localidade,
                modalidade=detalhe.modalidade if detalhe else preview.modalidade,
                descricao=detalhe.descricao if detalhe else None,
                gupy_external_id=detalhe.gupy_external_id if detalhe else None,
                filtro_id=filtro.id,
            )
            vaga, criada = await persistir_vaga(session, candidata)
            if criada:
                novas += 1
                pool: ArqRedis = await create_pool(get_redis_settings())
                try:
                    await pool.enqueue_job("match_score", vaga.id)
                finally:
                    await pool.close()
        await marcar_executado(session, filtro.id)

    log.info("scrape_search_done", filtro_id=filtro_id, novas=novas, total=len(previews))
    return novas


async def scrape_job(ctx: dict, url: str, chat_id: int) -> int:
    maker = get_session_maker()
    async with maker() as session:
        existente = await vaga_por_url(session, url)
        if existente is not None:
            pool: ArqRedis = await create_pool(get_redis_settings())
            try:
                await pool.enqueue_job("match_score", existente.id, chat_id)
            finally:
                await pool.close()
            return existente.id

    try:
        context = await get_context("gupy")
        detalhe = await parse_job_page(context, url=url)
    except Exception as e:
        log.error("scrape_job_failed", url=url, error=str(e))
        return 0

    candidata = VagaCandidata(
        url=detalhe.url,
        titulo=detalhe.titulo,
        empresa=detalhe.empresa,
        localidade=detalhe.localidade,
        modalidade=detalhe.modalidade,
        descricao=detalhe.descricao,
        gupy_external_id=detalhe.gupy_external_id,
    )
    async with maker() as session:
        vaga, _ = await persistir_vaga(session, candidata)

    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("match_score", vaga.id, chat_id)
    finally:
        await pool.close()
    return vaga.id
