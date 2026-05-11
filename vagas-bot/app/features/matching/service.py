import json

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.llm.client import get_llm
from app.core.llm.models import PROVIDER_MODELS
from app.core.logging import get_logger
from app.core.rag.embeddings import embed_texts
from app.features.cv.models import CV, CVChunk
from app.features.descoberta.models import Vaga
from app.features.matching.models import MatchResult
from app.features.matching.prompts import SYSTEM_PROMPT, USER_TEMPLATE

log = get_logger(__name__)

TOP_K_CHUNKS = 6


async def _retrieve_cv_chunks(
    session: AsyncSession, *, descricao: str, k: int = TOP_K_CHUNKS
) -> list[CVChunk]:
    embeddings = await embed_texts([descricao])
    emb = embeddings[0]

    cv_ativo = (
        await session.execute(select(CV).where(CV.ativo.is_(True)))
    ).scalar_one_or_none()
    if cv_ativo is None:
        return []

    distance = CVChunk.embedding.cosine_distance(emb).label("dist")
    stmt = (
        select(CVChunk)
        .where(CVChunk.cv_id == cv_ativo.id)
        .order_by(distance)
        .limit(k)
    )
    return list((await session.execute(stmt)).scalars())


def _parse_response(content: str) -> dict:
    txt = content.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:]
    return json.loads(txt.strip())


async def match_scoring(session: AsyncSession, vaga_id: int) -> MatchResult | None:
    vaga = await session.get(Vaga, vaga_id)
    if vaga is None or not vaga.descricao:
        log.warning("matching_skipped_no_vaga_or_descricao", vaga_id=vaga_id)
        return None

    existing = (
        await session.execute(
            select(MatchResult).where(MatchResult.vaga_id == vaga_id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    chunks = await _retrieve_cv_chunks(session, descricao=vaga.descricao)
    if not chunks:
        log.warning("matching_skipped_no_cv", vaga_id=vaga_id)
        return None

    chunks_text = "\n---\n".join(c.texto for c in chunks)
    user_msg = USER_TEMPLATE.format(
        titulo=vaga.titulo,
        empresa=vaga.empresa or "?",
        localidade=vaga.localidade or "?",
        modalidade=vaga.modalidade or "?",
        descricao=vaga.descricao[:4000],
        k=len(chunks),
        chunks=chunks_text,
    )

    llm = get_llm("FAST")
    resp = await llm.ainvoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ])
    try:
        parsed = _parse_response(resp.content)
        score = max(0, min(100, int(parsed["score"])))
        justificativa = str(parsed["justificativa"]).strip()
        citacoes = [str(c).strip() for c in parsed.get("citacoes", [])][:5]
    except (ValueError, KeyError, TypeError) as e:
        log.error("matching_parse_failed", vaga_id=vaga_id, error=str(e), raw=str(resp.content)[:300])
        return None

    provider = get_settings().llm_provider
    modelo = PROVIDER_MODELS[provider]["FAST"]

    mr = MatchResult(
        vaga_id=vaga.id,
        score=score,
        justificativa=justificativa,
        citacoes=citacoes,
        modelo=modelo,
    )
    session.add(mr)
    await session.commit()
    await session.refresh(mr)
    log.info("match_scored", vaga_id=vaga_id, score=score, citacoes=len(citacoes))
    return mr
