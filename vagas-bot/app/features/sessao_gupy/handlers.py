from telegram import Update
from telegram.ext import ContextTypes

from app.core.logging import get_logger
from app.core.telegram import admin_only

log = get_logger(__name__)

RELOGIN_MSG = (
    "Para (re)logar no Gupy:\n\n"
    "1) Em uma máquina com display, vá até a pasta do projeto e rode:\n"
    "   `python -m app.tools.gupy_login`\n\n"
    "2) Uma janela do Camoufox vai abrir. Faça login normalmente.\n\n"
    "3) Quando terminar, volte ao terminal e tecle ENTER. A sessão será "
    "criptografada e salva no banco.\n\n"
    "4) Confira aqui com /sessao."
)


@admin_only
async def relogin_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("relogin_requested", user_id=update.effective_user.id)
    await update.message.reply_text(RELOGIN_MSG, parse_mode="Markdown")
