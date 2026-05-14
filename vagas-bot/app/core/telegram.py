from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]


def admin_only(handler: Handler) -> Handler:
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = get_settings().telegram_admin_user_id
        user = update.effective_user
        if user is None or user.id != admin_id:
            log.warning("unauthorized_access",
                        user_id=getattr(user, "id", None),
                        username=getattr(user, "username", None))
            if update.message is not None:
                await update.message.reply_text("Não autorizado.")
            return
        return await handler(update, context)
    return wrapper


def build_application() -> Application:
    return (
        ApplicationBuilder()
        .token(get_settings().telegram_bot_token)
        .concurrent_updates(True)
        .get_updates_connect_timeout(20.0)
        .get_updates_read_timeout(40.0)
        .get_updates_write_timeout(20.0)
        .get_updates_pool_timeout(20.0)
        .connect_timeout(15.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(15.0)
        .build()
    )
