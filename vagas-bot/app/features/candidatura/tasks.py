import json
from pathlib import Path

from arq.connections import ArqRedis, create_pool
from sqlalchemy.ext.asyncio import AsyncSession

from app.browser.camoufox import open_context
from app.browser.flows.apply import (
    AppliedResult,
    PendingQuestion,
    apply_to_vaga,
)
from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.pending_question import pend_ctx_delete, pend_ctx_save
from app.core.redis import get_redis_settings
from app.features.candidatura.models import CandidaturaStatus
from app.features.candidatura.service import (
    contar_aplicadas_hoje,
    get_candidatura,
    marcar_aplicada,
    marcar_aplicando,
    marcar_falha,
    marcar_pergunta_pendente,
)
from app.features.descoberta.models import Vaga
from app.features.respostas.service import buscar_resposta, registrar_uso
from app.features.sessao_gupy.service import load_storage_state

log = get_logger(__name__)

SCREENSHOT_DIR = Path("/app/data/screenshots")


async def _build_answer_lookup(session: AsyncSession):
    async def lookup(pergunta: str) -> str | None:
        match = await buscar_resposta(session, pergunta=pergunta)
        if match is None:
            return None
        await registrar_uso(session, match.id)
        return match.resposta_texto
    return lookup


async def apply_job(ctx: dict, candidatura_id: int) -> str:
    settings = get_settings()
    maker = get_session_maker()

    async with maker() as session:
        cand = await get_candidatura(session, candidatura_id)
        if cand is None:
            log.warning("apply_job_missing", candidatura_id=candidatura_id)
            return "missing"
        if cand.status == CandidaturaStatus.APPLIED.value:
            return "already_applied"

        hoje = await contar_aplicadas_hoje(session)
        if hoje >= settings.daily_apply_limit:
            log.warning("apply_rate_limited", count=hoje, limit=settings.daily_apply_limit)
            return "rate_limited"

        vaga = await session.get(Vaga, cand.vaga_id)
        if vaga is None:
            await marcar_falha(session, candidatura_id, erro="vaga inexistente")
            return "no_vaga"

        storage_state_bytes = await load_storage_state(session)
        if storage_state_bytes is None:
            await marcar_falha(session, candidatura_id, erro="sem sessão Gupy ativa; rode /relogin")
            pool: ArqRedis = await create_pool(get_redis_settings())
            try:
                await pool.enqueue_job("notify_candidatura_falhou", candidatura_id)
            finally:
                await pool.close()
            return "no_session"

        await marcar_aplicando(session, candidatura_id)
        storage_state = json.loads(storage_state_bytes.decode())
        lookup = await _build_answer_lookup(session)
        url = vaga.url

    try:
        async with open_context(headless=True, storage_state=storage_state) as context:
            result = await apply_to_vaga(
                context,
                url=url,
                answer_lookup=lookup,
                screenshot_dir=SCREENSHOT_DIR,
                candidatura_id=candidatura_id,
            )
    except Exception as e:
        log.error("apply_failed", candidatura_id=candidatura_id, error=str(e))
        async with maker() as session:
            await marcar_falha(session, candidatura_id, erro=str(e))
        pool = await create_pool(get_redis_settings())
        try:
            await pool.enqueue_job("notify_candidatura_falhou", candidatura_id)
        finally:
            await pool.close()
        return "failed"

    async with maker() as session:
        if isinstance(result, AppliedResult):
            await marcar_aplicada(session, candidatura_id, screenshot=result.screenshot_path)
            log.info("apply_done", candidatura_id=candidatura_id, screenshot=result.screenshot_path)
            pool = await create_pool(get_redis_settings())
            try:
                await pool.enqueue_job("notify_candidatura_aplicada", candidatura_id)
            finally:
                await pool.close()
            return "applied"
        if isinstance(result, PendingQuestion):
            await marcar_pergunta_pendente(
                session,
                candidatura_id,
                pergunta=result.pergunta,
                field_id=result.field_id,
                screenshot=result.screenshot_path,
            )
            if result.prompt_extra:
                await pend_ctx_save(candidatura_id, result.prompt_extra)
            else:
                await pend_ctx_delete(candidatura_id)
            log.info(
                "apply_paused_on_question",
                candidatura_id=candidatura_id,
                pergunta=result.pergunta,
            )
            pool = await create_pool(get_redis_settings())
            try:
                await pool.enqueue_job("notify_pergunta_pendente", candidatura_id)
            finally:
                await pool.close()
            return "pending_question"
    return "unknown"
