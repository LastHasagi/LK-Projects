import re

from arq.connections import ArqRedis, create_pool
from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.descoberta.service import marcar_status
from app.features.filtros.service import listar_filtros

log = get_logger(__name__)

GUPY_URL_RE = re.compile(r"https?://[^\s]*gupy\.io/[^\s]+")


@admin_only
async def link_drop_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    match = GUPY_URL_RE.search(text)
    if not match:
        return
    url = match.group(0).rstrip(".,;")
    log.info("link_drop_received", url=url)
    await update.message.reply_text("Vou buscar essa vaga…")
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("scrape_job", url, update.effective_chat.id)
    finally:
        await pool.close()


async def vaga_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("vaga_ignorar:"):
        return
    if query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    vid = int(query.data.split(":", 1)[1])
    maker = get_session_maker()
    async with maker() as session:
        await marcar_status(session, vid, "ignorada")
    await query.answer("Ignorada.")
    await query.edit_message_text(f"Vaga #{vid} ignorada.")
    log.info("vaga_ignorada", vaga_id=vid)


@admin_only
async def insta_search_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    maker = get_session_maker()
    async with maker() as session:
        ativos = await listar_filtros(session, ativos=True)
    if not ativos:
        await update.message.reply_text(
            "Nenhum filtro ativo. Crie um com /filtros_add."
        )
        return
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        for f in ativos:
            await pool.enqueue_job("scrape_search", f.id)
    finally:
        await pool.close()
    nomes = ", ".join(f.nome for f in ativos)
    await update.message.reply_text(
        f"Disparei busca para {len(ativos)} filtro(s): {nomes}. "
        f"Vagas novas chegam em breve."
    )
    log.info("insta_search_dispatched", count=len(ativos))


link_drop_filter = filters.TEXT & filters.Regex(GUPY_URL_RE) & ~filters.COMMAND
link_drop_message_handler = MessageHandler(link_drop_filter, link_drop_handler)
vaga_ignorar_handler = CallbackQueryHandler(vaga_callback, pattern=r"^vaga_ignorar:\d+$")
