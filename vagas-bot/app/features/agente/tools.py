import json

from arq.connections import ArqRedis, create_pool
from langchain_core.tools import tool
from sqlalchemy import select

from app.core.db import get_session_maker
from app.core.rag.embeddings import embed_texts
from app.core.redis import get_redis_settings
from app.features.candidatura.service import listar_em_andamento
from app.features.descoberta.models import Vaga
from app.features.filtros.service import listar_filtros
from app.features.matching.models import MatchResult


@tool
async def buscar_vagas_semantica(query: str, limite: int = 5) -> str:
    """Busca vagas já descobertas usando similaridade semântica da descrição.
    Use quando o usuário perguntar por vagas de um tema (ex: 'vagas de backend python')."""
    embeddings = await embed_texts([query])
    emb = embeddings[0]
    maker = get_session_maker()
    async with maker() as session:
        distance = Vaga.descricao_embedding.cosine_distance(emb).label("dist")
        stmt = (
            select(Vaga, distance)
            .where(Vaga.descricao_embedding.isnot(None))
            .order_by(distance)
            .limit(limite)
        )
        rows = (await session.execute(stmt)).all()
    if not rows:
        return "Nenhuma vaga encontrada com essa descrição."
    out = []
    for v, dist in rows:
        out.append(
            f"#{v.id} {v.titulo} ({v.empresa}) — sim={1 - dist:.2f} — {v.url}"
        )
    return "\n".join(out)


@tool
async def explicar_fit(vaga_id: int) -> str:
    """Retorna o score de match e a justificativa para uma vaga específica."""
    maker = get_session_maker()
    async with maker() as session:
        mr = (
            await session.execute(
                select(MatchResult).where(MatchResult.vaga_id == vaga_id)
            )
        ).scalar_one_or_none()
    if mr is None:
        return f"Sem MatchResult para vaga #{vaga_id}."
    return (
        f"Score {mr.score}/100\n"
        f"Justificativa: {mr.justificativa}\n"
        f"Citações: {json.dumps(mr.citacoes, ensure_ascii=False)}"
    )


@tool
async def listar_candidaturas_em_andamento() -> str:
    """Lista candidaturas em andamento (queued, applying, pending_user_input)."""
    maker = get_session_maker()
    async with maker() as session:
        rows = await listar_em_andamento(session)
    if not rows:
        return "Nenhuma candidatura em andamento."
    return "\n".join(
        f"#{c.id} vaga={c.vaga_id} status={c.status} tentativas={c.tentativas}"
        for c in rows
    )


@tool
async def iniciar_busca_vagas() -> str:
    """Dispara busca imediata no Gupy para TODOS os filtros ativos.
    Use quando o usuário pedir para procurar vagas novas, atualizar, ou buscar agora.
    Não espera resultado — busca roda em background e cards chegam conforme prontos."""
    maker = get_session_maker()
    async with maker() as session:
        ativos = await listar_filtros(session, ativos=True)
    if not ativos:
        return "Nenhum filtro ativo. Use /filtros_add para criar um filtro antes."
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        for f in ativos:
            await pool.enqueue_job("scrape_search", f.id)
    finally:
        await pool.close()
    nomes = ", ".join(f.nome for f in ativos)
    return f"Busca disparada para {len(ativos)} filtro(s): {nomes}. Cards chegam em breve."


AGENT_TOOLS = [
    buscar_vagas_semantica,
    explicar_fit,
    listar_candidaturas_em_andamento,
    iniciar_busca_vagas,
]
