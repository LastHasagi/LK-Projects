from telegram import Update
from telegram.ext import ContextTypes

from app.core.logging import get_logger
from app.core.telegram import admin_only

log = get_logger(__name__)


@admin_only
async def start_handler(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    log.info("start_command", user_id=user.id, username=user.username)
    name = user.first_name or "admin"
    await update.message.reply_text(
        f"Olá, {name}. vagas-bot online. Use /admin para painel; /upload_cv (em breve)."
    )
