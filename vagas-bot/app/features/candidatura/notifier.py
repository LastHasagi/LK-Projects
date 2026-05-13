from telegram import Bot, InputFile

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.pending_question import pend_ctx_get, pend_question_save
from app.features.candidatura.service import get_candidatura

log = get_logger(__name__)


async def notify_pergunta_pendente(ctx: dict, candidatura_id: int) -> None:
    maker = get_session_maker()
    async with maker() as session:
        cand = await get_candidatura(session, candidatura_id)
    if cand is None or cand.pergunta_pendente is None:
        return
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    extra = await pend_ctx_get(cand.id)
    extra_block = f"\n\n{extra}" if extra else ""
    caption = (
        f"❓ *Pergunta nova na candidatura #{cand.id}*\n\n"
        f"_{cand.pergunta_pendente}_{extra_block}\n\n"
        f"↩️ *Responda esta mensagem* (long-press → Responder) para que "
        f"eu grave e retome. Mensagens normais NÃO viram resposta."
    )
    try:
        sent = None
        if cand.screenshot_path:
            try:
                with open(cand.screenshot_path, "rb") as f:
                    sent = await bot.send_photo(
                        chat_id=settings.telegram_admin_user_id,
                        photo=InputFile(f),
                        caption=caption[:1024],
                        parse_mode="Markdown",
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=15,
                    )
            except FileNotFoundError:
                log.warning(
                    "pergunta_screenshot_missing",
                    candidatura_id=cand.id,
                    path=cand.screenshot_path,
                )
            except Exception as e:
                log.warning(
                    "pergunta_screenshot_send_failed",
                    candidatura_id=cand.id,
                    error=str(e),
                )
        if sent is None:
            sent = await bot.send_message(
                chat_id=settings.telegram_admin_user_id,
                text=caption,
                parse_mode="Markdown",
            )
        await pend_question_save(sent.message_id, cand.id)
    finally:
        await bot.shutdown()


async def notify_candidatura_aplicada(ctx: dict, candidatura_id: int) -> None:
    maker = get_session_maker()
    async with maker() as session:
        cand = await get_candidatura(session, candidatura_id)
    if cand is None:
        return
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    try:
        msg = f"✅ Candidatura #{cand.id} aplicada (vaga {cand.vaga_id})."
        if cand.screenshot_path:
            try:
                with open(cand.screenshot_path, "rb") as f:
                    await bot.send_photo(
                        chat_id=settings.telegram_admin_user_id,
                        photo=InputFile(f),
                        caption=msg,
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=15,
                    )
                return
            except FileNotFoundError:
                pass
        await bot.send_message(chat_id=settings.telegram_admin_user_id, text=msg)
    finally:
        await bot.shutdown()


async def notify_candidatura_falhou(ctx: dict, candidatura_id: int) -> None:
    maker = get_session_maker()
    async with maker() as session:
        cand = await get_candidatura(session, candidatura_id)
    if cand is None:
        return
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    try:
        msg = (
            f"❌ Candidatura #{cand.id} falhou (vaga {cand.vaga_id}).\n\n"
            f"{cand.ultimo_erro or 'sem detalhes'}"
        )
        if cand.screenshot_path:
            try:
                with open(cand.screenshot_path, "rb") as f:
                    await bot.send_photo(
                        chat_id=settings.telegram_admin_user_id,
                        photo=InputFile(f),
                        caption=msg[:1024],
                        read_timeout=60,
                        write_timeout=60,
                        connect_timeout=15,
                    )
                return
            except FileNotFoundError:
                pass
        await bot.send_message(chat_id=settings.telegram_admin_user_id, text=msg)
    finally:
        await bot.shutdown()
