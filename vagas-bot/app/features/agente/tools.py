import hashlib
import json
import re
from typing import Annotated

from arq.connections import ArqRedis, create_pool
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.email_text import extract_emails
from app.core.pending_email import EMAIL_CONFIRM_PENDING_PREFIX, pend_email_save
from app.core.rag.embeddings import embed_texts
from app.core.redis import get_redis_settings
from app.features.agente.email_dispatch import dispatch_application_email
from app.features.agente.long_term_memory import (
    ALLOWED_CATEGORIES,
    put_fact,
    search_facts,
)
from app.features.candidatura.service import criar_candidatura, listar_em_andamento
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
    justificativa = (mr.justificativa or "")[:600]
    citacoes = (mr.citacoes or [])[:3]
    return (
        f"Score {mr.score}/100\n"
        f"Justificativa: {justificativa}\n"
        f"Citações: {json.dumps(citacoes, ensure_ascii=False)}"
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
async def candidatar_a_vaga(vaga_id: int) -> str:
    """Dispara a candidatura automatizada (Camoufox + Playwright) para uma vaga
    JÁ indexada (vinda de `buscar_vagas_semantica` ou descoberta). Use quando o
    usuário pedir para se candidatar a uma vaga com link Gupy, ou explicitamente
    referir-se a uma vaga pelo id. NÃO use para vagas que dependem de e-mail —
    para essas, use `preparar_envio_email_confirmacao`."""
    maker = get_session_maker()
    async with maker() as session:
        vaga = await session.get(Vaga, vaga_id)
        if vaga is None:
            return f"Vaga id={vaga_id} não existe no índice."
        cand = await criar_candidatura(session, vaga_id=vaga_id)
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("apply_job", cand.id)
    finally:
        await pool.close()
    return (
        f"Candidatura #{cand.id} enfileirada para a vaga '{vaga.titulo}' "
        f"({vaga.empresa or 'empresa desconhecida'}). O worker vai abrir a vaga "
        f"no Gupy, preencher os campos com respostas em memória e te perguntar "
        f"se aparecer algo novo."
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


_REGIME_RE = re.compile(r"\b(clt|pj|mei|pessoa\s+jur[ií]dica)\b", re.IGNORECASE)
_CURRENCY_RE = re.compile(r"(r\$|brl|reais)|(\d{1,3}[.,]?\d{0,3})", re.IGNORECASE)


def _validate_fato(fato: str, categoria: str) -> str | None:
    """Retorna mensagem de erro se inválido; None se ok."""
    if fato.count("R$") > 1 or len(_REGIME_RE.findall(fato)) > 1:
        return (
            "Fato composto detectado (múltiplos valores ou regimes na mesma "
            "string). Divida em fatos atômicos: salve UM fato por chamada."
        )
    if categoria == "compensacao_disponibilidade":
        has_money = bool(_CURRENCY_RE.search(fato))
        has_regime = bool(_REGIME_RE.search(fato))
        is_modalidade = any(
            w in fato.lower() for w in ("remoto", "híbrido", "hibrido", "presencial")
        )
        is_disponibilidade = any(
            w in fato.lower()
            for w in ("disponível", "disponibilidade", "dias", "imediato")
        )
        if not (has_money or has_regime or is_modalidade or is_disponibilidade):
            return (
                "Fato em 'compensacao_disponibilidade' deve conter valor, regime, "
                "modalidade ou disponibilidade. Use frase explícita."
            )
    return None


@tool
async def salvar_fato_usuario(
    fato: str,
    categoria: str,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Salva um fato duradouro do usuário em memória de longo prazo.

    REGRA: antes de chamar, MOSTRE ao usuário no chat o que vai salvar e PEÇA
    confirmação ("vou salvar 'X' como padrão, ok?"). Só chame após "sim/ok".

    Categorias permitidas:
    - `candidato`: nome completo, idade, localização, contato, linkedin,
      restrições de visto, idiomas. Um fato atômico por chamada.
    - `compensacao_disponibilidade`: UM valor de pretensão (com regime), OU
      modalidade preferida, OU disponibilidade. Nunca composto.

    Nunca salve: dúvidas pontuais, mensagens fugazes, lixo de conversa.
    Nunca salve fato COMPOSTO (ex.: 'R$13k CLT e R$17k PJ') — quebra em dois."""
    if categoria not in ALLOWED_CATEGORIES:
        return (
            f"Categoria inválida: {categoria}. Use uma de: "
            f"{', '.join(ALLOWED_CATEGORIES)}."
        )
    fato = fato.strip()
    if not fato:
        return "Fato vazio; nada a salvar."
    err = _validate_fato(fato, categoria)
    if err is not None:
        return f"Rejeitado: {err}"
    key = hashlib.sha1(fato.encode("utf-8")).hexdigest()[:16]
    await put_fact(store, key=key, fato=fato, categoria=categoria)
    return f"Fato salvo ({categoria}): {fato[:120]}"


@tool
async def buscar_fatos_relevantes(
    query: str,
    store: Annotated[BaseStore, InjectedStore()],
    k: int = 5,
) -> str:
    """Busca semanticamente fatos persistidos do usuário. Use antes de redigir
    e-mail de candidatura, responder pergunta de cadastro de vaga, ou quando o
    usuário fizer referência a algo que ele já tenha contado em outra conversa
    (nome, pretensão, localização etc.). Devolve até k fatos como JSON."""
    if not query.strip():
        return "[]"
    hits = await search_facts(store, query=query, k=k)
    return json.dumps(hits, ensure_ascii=False)


AGENT_TOOLS = [
    buscar_vagas_semantica,
    explicar_fit,
    listar_candidaturas_em_andamento,
    iniciar_busca_vagas,
    extrair_emails_do_texto,
    preparar_envio_email_confirmacao,
    candidatar_a_vaga,
    traduzir_cv_para_idioma,
    salvar_fato_usuario,
]
