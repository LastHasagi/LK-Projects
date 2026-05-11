from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rag.chunker import chunk_text, estimate_tokens, parse_pdf
from app.core.rag.embeddings import embed_texts
from app.features.cv.models import CV, CVChunk


async def ingest_cv_from_pdf(session: AsyncSession, *, pdf_path: str) -> CV:
    raw = parse_pdf(pdf_path)
    return await ingest_cv_text(session, raw_text=raw, source_path=pdf_path)


async def ingest_cv_text(
    session: AsyncSession, *, raw_text: str, source_path: str
) -> CV:
    chunks = chunk_text(raw_text, max_tokens=400, overlap_tokens=50)
    embeddings = await embed_texts(chunks) if chunks else []

    last = (
        await session.execute(select(CV).order_by(CV.versao.desc()))
    ).scalars().first()
    next_versao = (last.versao + 1) if last else 1

    cv = CV(versao=next_versao, path_pdf=source_path, ativo=False)
    session.add(cv)
    await session.flush()

    for idx, (texto, emb) in enumerate(zip(chunks, embeddings, strict=True)):
        session.add(
            CVChunk(
                cv_id=cv.id,
                ordem=idx,
                texto=texto,
                tokens=estimate_tokens(texto),
                embedding=emb,
            )
        )
    await session.commit()
    await session.refresh(cv)
    return cv


async def set_active_cv(session: AsyncSession, cv_id: int) -> None:
    await session.execute(update(CV).values(ativo=False))
    await session.execute(update(CV).where(CV.id == cv_id).values(ativo=True))
    await session.commit()


async def get_active_cv(session: AsyncSession) -> CV | None:
    stmt = select(CV).where(CV.ativo.is_(True))
    return (await session.execute(stmt)).scalar_one_or_none()
