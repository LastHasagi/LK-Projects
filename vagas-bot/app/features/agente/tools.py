import json

from arq.connections import ArqRedis, create_pool
from langchain_core.tools import tool
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.email_text import extract_emails
from app.core.pending_email import EMAIL_CONFIRM_PENDING_PREFIX, pend_email_save
from app.core.rag.embeddings import embed_texts
from app.core.redis import get_redis_settings
from app.features.agente.email_dispatch import dispatch_application_email
from app.features.candidatura.service import listar_em_andamento
from app.features.cv.service import get_active_cv
from app.features.cv.translation import (
    SUPPORTED_LANGS,
    CVTranslationError,
    get_or_create_translated_cv,
)
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


_MAX_EMAIL_BODY_CHARS = 50_000


@tool
def extrair_emails_do_texto(texto: str) -> str:
    """Lista e-mails em um texto. Use se o destinatário não for óbvio; se já houver um
    e-mail claro no post, pode redigir o rascunho sem obrigar o usuário a repetir o texto."""
    found = extract_emails(texto)
    if not found:
        return "Nenhum e-mail encontrado no texto."
    return json.dumps(found, ensure_ascii=False)


@tool
async def preparar_envio_email_confirmacao(
    destinatario: str,
    assunto: str,
    corpo: str,
    anexar_cv: bool = True,
    cv_lang: str | None = None,
) -> str:
    """Registra o rascunho final; o Telegram mostra botões Enviar/Cancelar.
    Chame quando o texto do e-mail estiver pronto. O SMTP dispara ao clicar em Enviar.

    cv_lang: passe 'pt', 'en', 'es' ou 'fr' se a vaga exigir o CV em idioma diferente
    do português. Antes, chame `traduzir_cv_para_idioma(cv_lang)`. Se não passar,
    o CV original (pt-BR) é anexado."""
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        return (
            "SMTP não configurado. Defina SMTP_USER e SMTP_PASSWORD no .env "
            "(Gmail: use senha de app em conta com 2FA)."
        )
    found = extract_emails(destinatario.strip())
    if len(found) != 1:
        return (
            "Informe exatamente um e-mail de destino "
            "(ou use extrair_emails_do_texto e peça qual usar)."
        )
    if len(corpo) > _MAX_EMAIL_BODY_CHARS:
        return f"Corpo muito longo (máx. {_MAX_EMAIL_BODY_CHARS} caracteres)."
    if cv_lang and cv_lang not in SUPPORTED_LANGS:
        return f"cv_lang inválido: {cv_lang}. Use {', '.join(SUPPORTED_LANGS)}."
    uid = await pend_email_save(
        {
            "destinatario": found[0],
            "assunto": assunto.strip()[:998],
            "corpo": corpo,
            "anexar_cv": anexar_cv,
            "cv_lang": cv_lang,
        }
    )
    return f"{EMAIL_CONFIRM_PENDING_PREFIX}{uid}"


@tool
async def enviar_candidatura_por_email(
    destinatario: str,
    assunto: str,
    corpo: str,
    anexar_cv: bool = True,
    cv_lang: str | None = None,
) -> str:
    """Envia e-mail na hora, sem botões. Use se o usuário confirmar só por texto.
    Fluxo normal: preferir `preparar_envio_email_confirmacao` após o rascunho.

    cv_lang: mesmo significado de `preparar_envio_email_confirmacao`."""
    return await dispatch_application_email(
        destinatario, assunto, corpo, anexar_cv=anexar_cv, cv_lang=cv_lang
    )


@tool
async def traduzir_cv_para_idioma(idioma: str) -> str:
    """Traduz o CV ativo para o idioma alvo e prepara o PDF para anexo.
    Use quando a vaga exigir CV em idioma diferente do português
    (ex.: 'submit your resume in English', 'currículum en español').
    Códigos aceitos: 'pt', 'en', 'es', 'fr'. Primeira chamada por idioma
    é cara (~10s); chamadas seguintes para o mesmo CV+idioma são cache.

    Depois desta tool, ao chamar `preparar_envio_email_confirmacao` ou
    `enviar_candidatura_por_email`, passe `cv_lang=<idioma>` para anexar
    o CV traduzido. Sem isso, o CV original em pt-BR é anexado."""
    if idioma not in SUPPORTED_LANGS:
        return f"Idioma não suportado: {idioma}. Use {', '.join(SUPPORTED_LANGS)}."
    maker = get_session_maker()
    async with maker() as session:
        cv = await get_active_cv(session)
        if cv is None:
            return "Nenhum CV ativo. Faça upload de um PDF via /cv antes de traduzir."
        try:
            translation = await get_or_create_translated_cv(
                session, cv_id=cv.id, target_lang=idioma
            )
        except CVTranslationError as e:
            return f"Falha ao traduzir CV: {e!s}"
    return (
        f"CV traduzido para '{idioma}' está pronto (cv_id={cv.id}, arquivo "
        f"{translation.pdf_path}). Ao montar o envio, passe cv_lang='{idioma}'."
    )


AGENT_TOOLS = [
    buscar_vagas_semantica,
    explicar_fit,
    listar_candidaturas_em_andamento,
    iniciar_busca_vagas,
    extrair_emails_do_texto,
    preparar_envio_email_confirmacao,
    enviar_candidatura_por_email,
    traduzir_cv_para_idioma,
]
