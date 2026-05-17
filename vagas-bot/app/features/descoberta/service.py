from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rag.embeddings import embed_texts
from app.features.descoberta.models import Vaga

SEMANTIC_DEDUPE_THRESHOLD = 0.92


@dataclass
class VagaCandidata:
    url: str
    titulo: str
    empresa: str | None
    localidade: str | None
    modalidade: str | None
    descricao: str | None
    gupy_external_id: str | None = None
    filtro_id: int | None = None
    ats: str = "gupy"


async def vaga_por_url(session: AsyncSession, url: str) -> Vaga | None:
    stmt = select(Vaga).where(Vaga.url == url)
    return (await session.execute(stmt)).scalar_one_or_none()


async def vaga_duplicata_semantica(
    session: AsyncSession,
    *,
    descricao_embedding: list[float],
    threshold: float = SEMANTIC_DEDUPE_THRESHOLD,
) -> Vaga | None:
    distance = Vaga.descricao_embedding.cosine_distance(descricao_embedding).label("dist")
    stmt = (
        select(Vaga, distance)
        .where(Vaga.descricao_embedding.isnot(None))
        .order_by(distance)
        .limit(1)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return None
    vaga, dist = row
    if (1 - dist) < threshold:
        return None
    return vaga


async def persistir_vaga(
    session: AsyncSession, candidata: VagaCandidata
) -> tuple[Vaga, bool]:
    existente = await vaga_por_url(session, candidata.url)
    if existente is not None:
        return existente, False

    embedding: list[float] | None = None
    if candidata.descricao:
        embeddings = await embed_texts([candidata.descricao])
        embedding = embeddings[0]
        dup = await vaga_duplicata_semantica(session, descricao_embedding=embedding)
        if dup is not None:
            return dup, False

    vaga = Vaga(
        url=candidata.url,
        gupy_external_id=candidata.gupy_external_id,
        empresa=candidata.empresa,
        titulo=candidata.titulo,
        localidade=candidata.localidade,
        modalidade=candidata.modalidade,
        descricao=candidata.descricao,
        descricao_embedding=embedding,
        filtro_id=candidata.filtro_id,
        ats=candidata.ats,
        status="novo",
    )
    session.add(vaga)
    await session.commit()
    await session.refresh(vaga)
    return vaga, True


async def marcar_status(session: AsyncSession, vaga_id: int, status: str) -> None:
    vaga = await session.get(Vaga, vaga_id)
    if vaga is not None:
        vaga.status = status
        await session.commit()
