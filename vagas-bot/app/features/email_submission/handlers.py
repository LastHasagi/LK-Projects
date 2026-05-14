from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app.core.db import get_session_maker
from app.core.telegram import admin_only
from app.features.email_submission.service import listar_recentes

_STATUS_EMOJI = {
    "pending": "⏳",
    "drafted": "✏️",
    "sent": "✅",
    "rejected": "🚫",
    "cancelled": "❌",
    "expired": "💨",
}


@admin_only
async def vagas_email_handler(
    update: Update, _ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    msg = update.effective_message
    chat_id = update.effective_chat.id if update.effective_chat else None
    if msg is None or chat_id is None:
        return
    maker = get_session_maker()
    async with maker() as session:
        subs = await listar_recentes(session, chat_id=chat_id, limit=20)
    if not subs:
        await msg.reply_text("Nenhuma submissão de e-mail nos últimos 30 dias.")
        return
    lines = ["📋 *Últimas submissões de e-mail*\n"]
    for s in subs:
        emoji = _STATUS_EMOJI.get(s.status, "•")
        dup = f" (dup #{s.duplicate_of})" if s.duplicate_of else ""
        when = s.created_at.strftime("%d/%m %H:%M")
        lines.append(
            f"{emoji} `#{s.id}` {when} → `{s.email_destinatario}` "
            f"`{s.status}`{dup}"
        )
    await msg.reply_text("\n".join(lines), parse_mode="Markdown")


vagas_email_command = CommandHandler("vagas_email", vagas_email_handler)
