from sqlalchemy import text
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app.core.db import get_engine
from app.core.logging import get_logger
from app.core.telegram import admin_only

log = get_logger(__name__)


@admin_only
async def reset_thread_handler(
    update: Update, _ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return
    thread = str(chat_id)
    engine = get_engine()
    async with engine.begin() as conn:
        a = await conn.execute(
            text("DELETE FROM checkpoint_writes WHERE thread_id = :t"),
            {"t": thread},
        )
        b = await conn.execute(
            text("DELETE FROM checkpoint_blobs WHERE thread_id = :t"),
            {"t": thread},
        )
        c = await conn.execute(
            text("DELETE FROM checkpoints WHERE thread_id = :t"),
            {"t": thread},
        )
    log.info(
        "thread_reset",
        thread=thread,
        writes=a.rowcount,
        blobs=b.rowcount,
        checkpoints=c.rowcount,
    )
    msg = update.effective_message
    if msg is not None:
        await msg.reply_text(
            f"🧹 Thread limpa ({a.rowcount} writes, {b.rowcount} blobs, "
            f"{c.rowcount} checkpoints). Próxima conversa começa do zero."
        )


reset_thread_command = CommandHandler("reset", reset_thread_handler)
