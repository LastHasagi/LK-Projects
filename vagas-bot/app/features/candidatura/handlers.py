from arq.connections import ArqRedis, create_pool
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.candidatura.models import CandidaturaStatus
from app.features.candidatura.service import (
    cancelar,
    candidatura_pelo_pergunta_pendente,
    criar_candidatura,
    listar_em_andamento,
    retomar_apos_resposta,
)
from app.features.respostas.service import upsert_resposta

log = get_logger(__name__)


async def vaga_candidatar_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("vaga_candidatar:"):
        return
    if query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    vaga_id = int(query.data.split(":", 1)[1])
    maker = get_session_maker()
    async with maker() as session:
        cand = await criar_candidatura(session, vaga_id=vaga_id)
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("apply_job", cand.id)
    finally:
        await pool.close()
    await query.answer("Candidatura iniciada.")
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(f"⏳ Aplicando #{cand.id}…", callback_data="noop")]]
        )
    )
    log.info("candidatura_enqueued", candidatura_id=cand.id, vaga_id=vaga_id)


@admin_only
async def pergunta_reply_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.text:
        return
    txt = msg.text.strip()
    if txt.startswith("/"):
        return

    maker = get_session_maker()
    async with maker() as session:
        cand = await candidatura_pelo_pergunta_pendente(session)
        if cand is None:
            return
        pergunta = cand.pergunta_pendente or ""
        await upsert_resposta(session, pergunta=pergunta, resposta=txt)
        await retomar_apos_resposta(session, cand.id)
        cand_id = cand.id

    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("apply_job", cand_id)
    finally:
        await pool.close()
    await msg.reply_text(f"Resposta salva. Retomando candidatura #{cand_id}…")
    log.info("pergunta_respondida", candidatura_id=cand_id, pergunta=pergunta)


@admin_only
async def vagas_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    maker = get_session_maker()
    async with maker() as session:
        em_andamento = await listar_em_andamento(session)
    if not em_andamento:
        await update.message.reply_text("Nenhuma candidatura em andamento.")
        return
    linhas = []
    botoes = []
    for c in em_andamento:
        status_icon = {
            CandidaturaStatus.QUEUED.value: "⏳",
            CandidaturaStatus.APPLYING.value: "🤖",
            CandidaturaStatus.PENDING_USER_INPUT.value: "❓",
        }.get(c.status, "·")
        linhas.append(
            f"{status_icon} #{c.id} vaga={c.vaga_id} status={c.status} "
            f"tentativas={c.tentativas}"
        )
        if c.pergunta_pendente:
            linhas.append(f"   pergunta: _{c.pergunta_pendente[:160]}_")
        botoes.append(
            [InlineKeyboardButton(f"🛑 cancelar #{c.id}", callback_data=f"cand_cancelar:{c.id}")]
        )
    await update.message.reply_text(
        "\n".join(linhas),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(botoes),
    )


async def cancelar_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("cand_cancelar:"):
        return
    if query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    cid = int(query.data.split(":", 1)[1])
    maker = get_session_maker()
    async with maker() as session:
        await cancelar(session, cid)
    await query.answer("Cancelada.")
    await query.edit_message_text(f"Candidatura #{cid} cancelada.")


vaga_candidatar_handler = CallbackQueryHandler(
    vaga_candidatar_callback, pattern=r"^vaga_candidatar:\d+$"
)
candidatura_cancelar_handler = CallbackQueryHandler(
    cancelar_callback, pattern=r"^cand_cancelar:\d+$"
)
pergunta_reply_message_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"gupy\.io"),
    pergunta_reply_handler,
)
