import asyncio
import time

from arq.connections import ArqRedis, create_pool
from langchain_core.messages import HumanMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, RetryAfter
from telegram.ext import ContextTypes, MessageHandler, filters

from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.email_text import extract_emails
from app.core.pending_email import pend_email_get, pend_email_save_existing
from app.core.pending_question import (
    pend_ctx_delete,
    pend_question_delete,
    pend_question_get,
)
from app.features.email_submission.models import SubmissionStatus
from app.features.email_submission.service import (
    criar_submissao,
    marcar_status,
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

_chat_locks: dict[int, asyncio.Lock] = {}


def _get_chat_lock(chat_id: int) -> asyncio.Lock:
    lock = _chat_locks.get(chat_id)
    if lock is None:
        lock = asyncio.Lock()
        _chat_locks[chat_id] = lock
    return lock


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

    chat_id = update.effective_chat.id
    chat_lock = _get_chat_lock(chat_id)
    if chat_lock.locked():
        log.info("agent_queueing", chat_id=chat_id)
    async with chat_lock:
        await _run_agent_turn(update, msg, txt)


async def _run_agent_turn(update: Update, msg, txt: str) -> None:
    graph = get_graph()
    chat_id = update.effective_chat.id
    config = {"configurable": {"thread_id": str(chat_id)}}
    emails_in_turn = list(dict.fromkeys(extract_emails(txt)))

    submission_id: int | None = None
    duplicate_info: str | None = None
    if len(emails_in_turn) == 1:
        maker = get_session_maker()
        async with maker() as session:
            sub, dup = await criar_submissao(
                session,
                chat_id=chat_id,
                email=emails_in_turn[0],
                raw_text=txt,
            )
            submission_id = sub.id
            if dup is not None:
                duplicate_info = (
                    f"⚠️ Esta vaga é DUPLICATA da submissão #{dup.id} "
                    f"(status={dup.status}, criada em "
                    f"{dup.created_at.isoformat(timespec='minutes')}). "
                    "Informe o usuário e pergunte se quer reaproveitar o "
                    "rascunho anterior, refazer com ajustes, ou descartar. "
                    "NÃO gere rascunho automaticamente."
                )

    constraint_parts: list[str] = []
    if submission_id is not None:
        constraint_parts.append(f"Submissão atual: #{submission_id}.")
    if emails_in_turn:
        constraint_parts.append(
            f"Emails detectados na mensagem AGORA: {emails_in_turn}. "
            "Destinatário deve ser um destes; nunca reaproveite e-mail de "
            "turnos anteriores. Múltiplos emails = pergunte qual usar."
        )
    if duplicate_info:
        constraint_parts.append(duplicate_info)

    if constraint_parts:
        composed_input: list = [
            HumanMessage(content="ESCOPO DO TURNO:\n" + "\n\n".join(constraint_parts)),
            HumanMessage(content=txt),
        ]
    else:
        composed_input = [HumanMessage(content=txt)]
    placeholder = None
    try:
        placeholder = await msg.reply_text("✍️ pensando…")
    except Exception:
        placeholder = None

    final_buffer = ""
    last_edit = 0.0
    last_rendered = ""
    EDIT_INTERVAL = 1.0
    final_state: dict | None = None
    try:
        async for event in graph.astream_events(
            {"messages": composed_input},
            config=config,
            version="v2",
        ):
            etype = event.get("event")
            metadata = event.get("metadata") or {}
            node = metadata.get("langgraph_node")
            if etype == "on_chat_model_start" and node == "agent":
                final_buffer = ""
            elif etype == "on_chat_model_stream" and node == "agent":
                chunk = (event.get("data") or {}).get("chunk")
                if chunk is not None:
                    content = chunk.content
                    if isinstance(content, str) and content:
                        final_buffer += content
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and isinstance(
                                part.get("text"), str
                            ):
                                final_buffer += part["text"]
                now = time.monotonic()
                if (
                    placeholder is not None
                    and final_buffer.strip()
                    and (now - last_edit) >= EDIT_INTERVAL
                    and final_buffer != last_rendered
                ):
                    try:
                        await placeholder.edit_text(final_buffer)
                        last_rendered = final_buffer
                        last_edit = now
                    except RetryAfter as ra:
                        await asyncio.sleep(getattr(ra, "retry_after", 1.0))
                    except BadRequest:
                        pass
                    except Exception:
                        pass
            elif etype == "on_chain_end" and event.get("name") == "LangGraph":
                final_state = (event.get("data") or {}).get("output")
    except Exception as e:
        log.error("agent_failed", error=str(e))
        if placeholder is not None:
            try:
                await placeholder.delete()
            except Exception:
                pass
        await msg.reply_text(f"Falhei no agente: {e}")
        return

    messages = (final_state or {}).get("messages") or []
    last = messages[-1] if messages else None
    reply = (
        _message_content_to_str(getattr(last, "content", "") if last else "")
        or final_buffer
    )
    pending_uuid = extract_pending_email_uuid_from_messages(messages)

    if pending_uuid:
        payload = await pend_email_get(pending_uuid)
        if payload is None:
            log.warning("pending_email_missing_on_render", uid=pending_uuid)
            pending_uuid = None
        elif emails_in_turn:
            destinatario = (payload.get("destinatario") or "").strip().lower()
            allowed = {e.lower() for e in emails_in_turn}
            if destinatario and destinatario not in allowed:
                log.warning(
                    "pending_email_destinatario_mismatch",
                    uid=pending_uuid,
                    destinatario=destinatario,
                    emails_in_turn=list(allowed),
                )
                pending_uuid = None
                payload = None
                if placeholder is not None:
                    try:
                        await placeholder.delete()
                    except Exception:
                        pass
                await msg.reply_text(
                    "⚠️ O destinatário do rascunho não bate com nenhum e-mail "
                    "na sua mensagem atual. Rascunho descartado pra evitar "
                    "envio para o recrutador errado. Tente colar a vaga "
                    "isolada ou me diga explicitamente o destino."
                )
                return

    if pending_uuid and payload is not None:
        if submission_id is not None:
            payload["submission_id"] = submission_id
            await pend_email_save_existing(pending_uuid, payload)
            maker = get_session_maker()
            async with maker() as session:
                await marcar_status(
                    session,
                    submission_id=submission_id,
                    status=SubmissionStatus.DRAFTED,
                    pending_email_uid=pending_uuid,
                )
        if placeholder is not None:
            try:
                await placeholder.delete()
            except Exception:
                pass
        draft_block = (
            "📨 *Rascunho do e-mail*\n\n"
            f"*Destinatário:* `{payload['destinatario']}`\n"
            f"*Assunto:* {payload['assunto']}\n\n"
            f"*Corpo:*\n```\n{payload['corpo']}\n```\n\n"
            "Aprove para enviar direto (sem custo de IA). "
            "Rejeite para revisar com motivo."
        )
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Aprovar e enviar",
                        callback_data=f"email:send:{pending_uuid}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "✏️ Rejeitar (revisar)",
                        callback_data=f"email:reject:{pending_uuid}",
                    )
                ],
            ]
        )
        await msg.reply_text(draft_block, reply_markup=markup, parse_mode="Markdown")
        return

    if reply and placeholder is not None and reply != last_rendered:
        try:
            await placeholder.edit_text(reply)
            return
        except Exception:
            try:
                await placeholder.delete()
            except Exception:
                pass
            await msg.reply_text(reply)
            return
    if reply and placeholder is None:
        await msg.reply_text(reply)
        return
    if not reply and placeholder is not None:
        try:
            await placeholder.delete()
        except Exception:
            pass


conversational_message_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"gupy\.io"),
    conversational_handler,
)
