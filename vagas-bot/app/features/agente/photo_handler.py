import asyncio
import base64
import json
from typing import Any

from langchain_core.messages import HumanMessage
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, MessageHandler, filters

from app.core.logging import get_logger
from app.core.pending_email import pend_email_get
from app.core.redis import get_redis
from app.core.telegram import admin_only
from app.features.agente.email_handlers import extract_pending_email_uuid_from_messages
from app.features.agente.graph import get_graph
from app.features.agente.handlers import _message_content_to_str

log = get_logger(__name__)

_GROUP_PREFIX = "vagas:photo_group:"
_GROUP_TTL = 30
_DEBOUNCE_S = 1.5
_MAX_PHOTOS_PER_TURN = 8


async def _download_b64(bot, file_id: str) -> tuple[str, str]:
    file = await bot.get_file(file_id)
    data: bytes = await file.download_as_bytearray()
    mime = "image/jpeg"
    if file.file_path and file.file_path.lower().endswith(".png"):
        mime = "image/png"
    elif file.file_path and file.file_path.lower().endswith(".webp"):
        mime = "image/webp"
    b64 = base64.b64encode(bytes(data)).decode("ascii")
    return mime, b64


def _build_multimodal_content(
    text: str, images: list[tuple[str, str]]
) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    if text.strip():
        parts.append({"type": "text", "text": text})
    else:
        parts.append(
            {
                "type": "text",
                "text": "Analise a(s) imagem(ns). Pode ser um post de vaga, "
                "screenshot do Gupy ou outro contexto. Aja conforme o conteúdo "
                "(redigir e-mail, listar, etc.) seguindo as regras do sistema.",
            }
        )
    for mime, b64 in images:
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
            }
        )
    return parts


async def _process_photos(
    update: Update, file_ids: list[str], caption: str
) -> None:
    msg = update.effective_message
    if msg is None:
        return
    placeholder = None
    try:
        placeholder = await msg.reply_text(
            f"🖼️ analisando {len(file_ids)} imagem(ns)…"
        )
    except Exception:
        placeholder = None

    bot = msg.get_bot()
    images: list[tuple[str, str]] = []
    for fid in file_ids[:_MAX_PHOTOS_PER_TURN]:
        try:
            images.append(await _download_b64(bot, fid))
        except Exception as e:
            log.warning("photo_download_failed", file_id=fid, error=str(e))

    content = _build_multimodal_content(caption, images)

    graph = get_graph()
    config = {"configurable": {"thread_id": str(update.effective_chat.id)}}
    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=content)]},
            config=config,
        )
    except Exception as e:
        log.error("agent_failed_on_photo", error=str(e))
        if placeholder is not None:
            try:
                await placeholder.delete()
            except Exception:
                pass
        await msg.reply_text(f"Falhei no agente: {e}")
        return

    if placeholder is not None:
        try:
            await placeholder.delete()
        except Exception:
            pass

    messages = result.get("messages") or []
    last = messages[-1] if messages else None
    reply = _message_content_to_str(getattr(last, "content", "") if last else "")
    pending_uuid = extract_pending_email_uuid_from_messages(messages)

    if pending_uuid:
        payload = await pend_email_get(pending_uuid)
        if payload is None:
            pending_uuid = None
        else:
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
            await msg.reply_text(
                draft_block, reply_markup=markup, parse_mode="Markdown"
            )
            return

    if reply:
        await msg.reply_text(reply)


@admin_only
async def photo_message_handler(
    update: Update, _ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    msg = update.effective_message
    if msg is None or not msg.photo:
        return
    photo = msg.photo[-1]
    caption = (msg.caption or "").strip()
    media_group = msg.media_group_id

    log.info(
        "photo_received",
        chat_id=update.effective_chat.id,
        media_group=media_group,
        has_caption=bool(caption),
        file_size=getattr(photo, "file_size", None),
    )

    if not media_group:
        await _process_photos(update, [photo.file_id], caption)
        return

    r = get_redis()
    key = _GROUP_PREFIX + media_group
    payload = json.dumps({"file_id": photo.file_id, "caption": caption})
    await r.rpush(key, payload)
    await r.expire(key, _GROUP_TTL)

    size_before = await r.llen(key)
    await asyncio.sleep(_DEBOUNCE_S)
    size_after = await r.llen(key)

    if size_after != size_before:
        return

    raw_items = await r.lrange(key, 0, -1)
    await r.delete(key)
    file_ids: list[str] = []
    captions: list[str] = []
    for raw in raw_items:
        if isinstance(raw, bytes):
            raw = raw.decode()
        data = json.loads(raw)
        file_ids.append(data["file_id"])
        if data.get("caption"):
            captions.append(data["caption"])
    combined_caption = "\n".join(c for c in captions if c)
    await _process_photos(update, file_ids, combined_caption)


photo_message_handler_instance = MessageHandler(filters.PHOTO, photo_message_handler)
