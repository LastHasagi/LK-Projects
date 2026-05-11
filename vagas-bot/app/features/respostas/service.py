from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rag.embeddings import embed_texts
from app.features.respostas.models import RespostaCustom

SIM_THRESHOLD = 0.88


async def upsert_resposta(
    session: AsyncSession, *, pergunta: str, resposta: str
) -> RespostaCustom:
    embeddings = await embed_texts([pergunta])
    emb = embeddings[0]

    existing = await buscar_resposta(session, pergunta=pergunta, _embedding=emb)
    if existing is not None:
        existing.resposta_texto = resposta
        existing.pergunta_texto = pergunta
        await session.commit()
        await session.refresh(existing)
        return existing

    row = RespostaCustom(
        pergunta_texto=pergunta,
        pergunta_embedding=emb,
        resposta_texto=resposta,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def buscar_resposta(
    session: AsyncSession,
    *,
    pergunta: str,
    threshold: float = SIM_THRESHOLD,
    _embedding: list[float] | None = None,
) -> RespostaCustom | None:
    emb = _embedding
    if emb is None:
        embeddings = await embed_texts([pergunta])
        emb = embeddings[0]
    distance = RespostaCustom.pergunta_embedding.cosine_distance(emb).label("dist")
    stmt = (
        select(RespostaCustom, distance)
        .order_by(distance)
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    resposta, dist = row
    if (1 - dist) < threshold:
        return None
    return resposta


async def registrar_uso(session: AsyncSession, resposta_id: int) -> None:
    await session.execute(
        update(RespostaCustom)
        .where(RespostaCustom.id == resposta_id)
        .values(
            vezes_usada=RespostaCustom.vezes_usada + 1,
            ultima_usada_em=datetime.now(timezone.utc),
        )
    )
    await session.commit()


async def listar_respostas(session: AsyncSession) -> list[RespostaCustom]:
    stmt = select(RespostaCustom).order_by(
        RespostaCustom.ultima_usada_em.desc().nullslast()
    )
    return list((await session.execute(stmt)).scalars())


async def remover_resposta(session: AsyncSession, resposta_id: int) -> None:
    obj = await session.get(RespostaCustom, resposta_id)
    if obj is not None:
        await session.delete(obj)
        await session.commit()
