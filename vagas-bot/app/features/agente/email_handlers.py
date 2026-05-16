from telegram import ForceReply, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.pending_email import (
    EMAIL_CONFIRM_PENDING_PREFIX,
    pend_email_delete,
    pend_email_get,
    revision_set,
)
from app.features.agente.email_dispatch import dispatch_application_email
from app.features.email_submission.models import SubmissionStatus
from app.features.email_submission.service import marcar_status_por_uid
from langchain_core.messages import HumanMessage, ToolMessage

log = get_logger(__name__)


def extract_pending_email_uuid_from_messages(messages: list) -> str | None:
    """Se a tool de preparação de e-mail rodou no TURNO atual, devolve o uuid.

    Para detectar 'turno atual', escaneia em ordem reversa e PARA ao bater no
    HumanMessage mais recente — sinais de turnos anteriores não são considerados.
    """
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return None
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
    if len(parts) != 3 or parts[1] not in ("send", "cancel", "reject"):
        return
    action, uid = parts[1], parts[2]
    if action == "cancel":
        await pend_email_delete(uid)
        await _set_submission_status(uid, SubmissionStatus.CANCELLED)
        await query.answer("Cancelado.")
        await query.edit_message_reply_markup(reply_markup=None)
        log.info("email_confirm_cancel", pending_id=uid)
        return
    if action == "reject":
        await pend_email_delete(uid)
        await _set_submission_status(uid, SubmissionStatus.REJECTED)
        chat_id_for_flag = update.effective_chat.id if update.effective_chat else None
        if chat_id_for_flag is not None:
            await revision_set(chat_id_for_flag)
        await query.answer("Rejeitado — me diga o motivo.")
        await query.edit_message_reply_markup(reply_markup=None)
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is not None:
            await query.get_bot().send_message(
                chat_id=chat_id,
                text=(
                    "✏️ Rascunho rejeitado. *Responda esta mensagem* dizendo o "
                    "que ajustar (tom, conteúdo, pretensão, etc.) que eu "
                    "reformulo e te mostro o novo rascunho."
                ),
                parse_mode="Markdown",
                reply_markup=ForceReply(
                    selective=True,
                    input_field_placeholder="O que ajustar no e-mail...",
                ),
            )
        log.info("email_confirm_reject", pending_id=uid)
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
        cv_lang=payload.get("cv_lang"),
    )
    if result.startswith("E-mail enviado"):
        await pend_email_delete(uid)
        await _set_submission_status(uid, SubmissionStatus.SENT)
        await query.answer("Enviado.")
        await query.edit_message_reply_markup(reply_markup=None)
        log.info("email_confirm_send", to=payload.get("destinatario"))
    else:
        await query.answer(result[:200], show_alert=True)
        log.warning("email_confirm_send_failed", error=result[:500])


async def _set_submission_status(uid: str, status: SubmissionStatus) -> None:
    maker = get_session_maker()
    async with maker() as session:
        await marcar_status_por_uid(
            session, pending_email_uid=uid, status=status
        )


email_inline_handler = CallbackQueryHandler(
    email_inline_callback,
    pattern=r"^email:(send|cancel|reject):[\w-]+$",
)
