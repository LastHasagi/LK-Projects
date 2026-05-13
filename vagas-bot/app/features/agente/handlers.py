from arq.connections import ArqRedis, create_pool
from langchain_core.messages import HumanMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, MessageHandler, filters

from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.pending_question import (
    pend_ctx_delete,
    pend_question_delete,
    pend_question_get,
)
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.agente.email_handlers import extract_pending_email_uuid_from_messages
from app.features.agente.graph import get_graph
from app.features.candidatura.service import (
    get_candidatura,
    retomar_apos_resposta,
)
from app.features.respostas.service import upsert_resposta

log = get_logger(__name__)


def _message_content_to_str(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
        return "".join(parts)
    return str(content)


@admin_only
async def conversational_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.text:
        return
    txt = msg.text.strip()
    log.info("conv_msg_received", chat_id=update.effective_chat.id, len=len(txt))

    reply_to = msg.reply_to_message
    cand_id: int | None = None
    if reply_to is not None:
        mapped = await pend_question_get(reply_to.message_id)
        if mapped is not None:
            maker = get_session_maker()
            async with maker() as session:
                pending = await get_candidatura(session, mapped)
                if pending is not None and pending.pergunta_pendente is not None:
                    pergunta = pending.pergunta_pendente
                    await upsert_resposta(session, pergunta=pergunta, resposta=txt)
                    await retomar_apos_resposta(session, pending.id)
                    cand_id = pending.id
            if cand_id is not None:
                await pend_question_delete(reply_to.message_id)
                await pend_ctx_delete(cand_id)
    if cand_id is not None:
        pool: ArqRedis = await create_pool(get_redis_settings())
        try:
            await pool.enqueue_job("apply_job", cand_id)
        finally:
            await pool.close()
        await msg.reply_text(f"Resposta salva. Retomando candidatura #{cand_id}…")
        log.info("pergunta_respondida", candidatura_id=cand_id)
        return

    graph = get_graph()
    config = {"configurable": {"thread_id": str(update.effective_chat.id)}}
    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=txt)]},
            config=config,
        )
        messages = result.get("messages") or []
        last = messages[-1] if messages else None
        reply = _message_content_to_str(getattr(last, "content", "") if last else "")
        pending_uuid = extract_pending_email_uuid_from_messages(messages)
    except Exception as e:
        log.error("agent_failed", error=str(e))
        await msg.reply_text(f"Falhei no agente: {e}")
        return

    if not reply and pending_uuid:
        reply = "Confirme o envio do e-mail abaixo."

    if reply or pending_uuid:
        markup = None
        if pending_uuid:
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Enviar", callback_data=f"email:send:{pending_uuid}"
                        ),
                        InlineKeyboardButton(
                            "Cancelar", callback_data=f"email:cancel:{pending_uuid}"
                        ),
                    ]
                ]
            )
        if pending_uuid and reply:
            reply = f"{reply}\n\nUse os botões abaixo para Enviar ou Cancelar."
        await msg.reply_text(reply or "...", reply_markup=markup)


conversational_message_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"gupy\.io"),
    conversational_handler,
)
