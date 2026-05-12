from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.pending_email import (
    EMAIL_CONFIRM_PENDING_PREFIX,
    pend_email_delete,
    pend_email_get,
)
from app.features.agente.email_dispatch import dispatch_application_email
from langchain_core.messages import ToolMessage

log = get_logger(__name__)


def extract_pending_email_uuid_from_messages(messages: list) -> str | None:
    """Se a última tool de preparação de e-mail rodou nesta volta, devolve o uuid."""
    for m in reversed(messages):
        if isinstance(m, ToolMessage):
            c = (m.content or "").strip()
            if c.startswith(EMAIL_CONFIRM_PENDING_PREFIX):
                return c[len(EMAIL_CONFIRM_PENDING_PREFIX) :].strip()
    return None


async def email_inline_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("email:"):
        return
    if query.from_user is None or query.from_user.id != get_settings().telegram_admin_user_id:
        await query.answer("Não autorizado.", show_alert=True)
        return
    parts = query.data.split(":", 2)
    if len(parts) != 3 or parts[1] not in ("send", "cancel"):
        return
    action, uid = parts[1], parts[2]
    if action == "cancel":
        await pend_email_delete(uid)
        await query.answer("Cancelado.")
        await query.edit_message_reply_markup(reply_markup=None)
        log.info("email_confirm_cancel", pending_id=uid)
        return
    payload = await pend_email_get(uid)
    if payload is None:
        await query.answer("Rascunho expirou ou já foi usado.", show_alert=True)
        return
    result = await dispatch_application_email(
        payload["destinatario"],
        payload["assunto"],
        payload["corpo"],
        anexar_cv=bool(payload.get("anexar_cv", True)),
    )
    if result.startswith("E-mail enviado"):
        await pend_email_delete(uid)
        await query.answer("Enviado.")
        await query.edit_message_reply_markup(reply_markup=None)
        log.info("email_confirm_send", to=payload.get("destinatario"))
    else:
        await query.answer(result[:200], show_alert=True)
        log.warning("email_confirm_send_failed", error=result[:500])


email_inline_handler = CallbackQueryHandler(
    email_inline_callback,
    pattern=r"^email:(send|cancel):[\w-]+$",
)
