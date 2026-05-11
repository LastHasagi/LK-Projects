from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.telegram import admin_only
from app.features.respostas.service import listar_respostas, remover_resposta

log = get_logger(__name__)


@admin_only
async def respostas_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    maker = get_session_maker()
    async with maker() as session:
        rows = await listar_respostas(session)
    if not rows:
        await update.message.reply_text(
            "Sem respostas salvas. Elas aparecem aqui conforme você responde "
            "perguntas custom durante candidaturas."
        )
        return
    linhas = []
    botoes = []
    for r in rows[:20]:
        preview_p = (r.pergunta_texto[:60] + "…") if len(r.pergunta_texto) > 60 else r.pergunta_texto
        preview_r = (r.resposta_texto[:60] + "…") if len(r.resposta_texto) > 60 else r.resposta_texto
        linhas.append(f"#{r.id} · _{preview_p}_\n→ {preview_r}\n(usada {r.vezes_usada}x)")
        botoes.append([InlineKeyboardButton(f"🗑 remover #{r.id}", callback_data=f"resposta_del:{r.id}")])
    await update.message.reply_text(
        "\n\n".join(linhas),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(botoes),
    )


async def respostas_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data:
        return
    if query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    if not query.data.startswith("resposta_del:"):
        return
    rid = int(query.data.split(":", 1)[1])
    maker = get_session_maker()
    async with maker() as session:
        await remover_resposta(session, rid)
    await query.answer("Removida.")
    await query.edit_message_text(f"Resposta #{rid} removida.")
    log.info("resposta_removed", resposta_id=rid)


respostas_del_handler = CallbackQueryHandler(respostas_callback, pattern=r"^resposta_del:\d+$")
