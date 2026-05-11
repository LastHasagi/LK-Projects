from arq.connections import ArqRedis, create_pool
from langchain_core.messages import HumanMessage
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.agente.graph import get_graph
from app.features.candidatura.service import (
    candidatura_pelo_pergunta_pendente,
    retomar_apos_resposta,
)
from app.features.respostas.service import upsert_resposta

log = get_logger(__name__)


@admin_only
async def conversational_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if msg is None or not msg.text:
        return
    txt = msg.text.strip()

    maker = get_session_maker()
    async with maker() as session:
        pending = await candidatura_pelo_pergunta_pendente(session)
        if pending is not None:
            pergunta = pending.pergunta_pendente or ""
            await upsert_resposta(session, pergunta=pergunta, resposta=txt)
            await retomar_apos_resposta(session, pending.id)
            cand_id = pending.id
    if pending is not None:
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
        reply = result["messages"][-1].content if result.get("messages") else ""
    except Exception as e:
        log.error("agent_failed", error=str(e))
        await msg.reply_text(f"Falhei no agente: {e}")
        return

    if reply:
        await msg.reply_text(reply)


conversational_message_handler = MessageHandler(
    filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"gupy\.io"),
    conversational_handler,
)
