from pathlib import Path

from arq.connections import ArqRedis, create_pool
from sqlalchemy import func, select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.pending_cv_upload import (
    pend_cv_delete,
    pend_cv_get,
    pend_cv_save,
)
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.cv.models import CVChunk
from app.features.cv.service import get_active_cv
from app.features.cv.translation import (
    CVTranslationError,
    save_user_provided_translation,
)

log = get_logger(__name__)

CV_DIR = Path("/app/data/cv")
TRANSLATION_DIR = Path("/app/data/cv_translations")


@admin_only
async def upload_cv_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    doc = msg.document
    if doc is None or not (doc.file_name or "").lower().endswith(".pdf"):
        await msg.reply_text("Envie um PDF como documento (não como foto).")
        return
    CV_DIR.mkdir(parents=True, exist_ok=True)
    file = await doc.get_file()
    dest = CV_DIR / f"{update.effective_user.id}_{doc.file_unique_id}.pdf"
    await file.download_to_drive(custom_path=str(dest))
    log.info("cv_uploaded", path=str(dest), size=doc.file_size)

    uid = await pend_cv_save({"path": str(dest), "file_name": doc.file_name})

    maker = get_session_maker()
    async with maker() as session:
        active = await get_active_cv(session)
    active_label = (
        f"v{active.versao}" if active is not None else "nenhum CV ativo"
    )

    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📄 CV novo (substitui ativo)",
                    callback_data=f"cv:new:{uid}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🇬🇧 Tradução EN", callback_data=f"cv:tr:en:{uid}"
                ),
                InlineKeyboardButton(
                    "🇪🇸 Tradução ES", callback_data=f"cv:tr:es:{uid}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🇫🇷 Tradução FR", callback_data=f"cv:tr:fr:{uid}"
                ),
                InlineKeyboardButton(
                    "❌ Cancelar", callback_data=f"cv:cancel:{uid}"
                ),
            ],
        ]
    )
    await msg.reply_text(
        f"📎 PDF recebido: `{doc.file_name}`\nAtivo: {active_label}\n\n"
        f"O que é este PDF?",
        reply_markup=markup,
        parse_mode="Markdown",
    )


async def cv_upload_callback(
    update: Update, _ctx: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if query is None or not query.data or not query.data.startswith("cv:"):
        return
    if (
        query.from_user is None
        or query.from_user.id != get_settings().telegram_admin_user_id
    ):
        await query.answer("Não autorizado.", show_alert=True)
        return

    parts = query.data.split(":")
    if len(parts) < 3:
        return
    action = parts[1]

    if action == "cancel":
        uid = parts[2]
        data = await pend_cv_get(uid)
        if data is not None:
            try:
                Path(data["path"]).unlink(missing_ok=True)
            except Exception:
                pass
            await pend_cv_delete(uid)
        await query.answer("Cancelado.")
        await query.edit_message_text("❌ Upload cancelado.")
        return

    if action == "new":
        uid = parts[2]
        data = await pend_cv_get(uid)
        if data is None:
            await query.answer("Upload expirado.", show_alert=True)
            return
        await pend_cv_delete(uid)
        pool: ArqRedis = await create_pool(get_redis_settings())
        try:
            await pool.enqueue_job("reindex_cv", data["path"])
        finally:
            await pool.close()
        await query.answer("Indexando…")
        await query.edit_message_text(
            f"📄 Indexando como CV novo: `{data['file_name']}`",
            parse_mode="Markdown",
        )
        log.info("cv_upload_as_new", path=data["path"])
        return

    if action == "tr":
        if len(parts) != 4:
            return
        lang, uid = parts[2], parts[3]
        data = await pend_cv_get(uid)
        if data is None:
            await query.answer("Upload expirado.", show_alert=True)
            return

        maker = get_session_maker()
        async with maker() as session:
            active = await get_active_cv(session)
            if active is None:
                await query.answer(
                    "Sem CV ativo. Suba um CV base antes.", show_alert=True
                )
                return
            TRANSLATION_DIR.mkdir(parents=True, exist_ok=True)
            dest = TRANSLATION_DIR / f"{active.id}_{lang}.pdf"
            try:
                src = Path(data["path"])
                dest.write_bytes(src.read_bytes())
                src.unlink(missing_ok=True)
            except Exception as e:
                await query.answer(f"Falha ao mover PDF: {e}", show_alert=True)
                return
            try:
                await save_user_provided_translation(
                    session,
                    cv_id=active.id,
                    target_lang=lang,
                    pdf_path=str(dest),
                )
            except CVTranslationError as e:
                await query.answer(str(e)[:200], show_alert=True)
                return
        await pend_cv_delete(uid)
        await query.answer("Salvo.")
        await query.edit_message_text(
            f"🌍 Salvo como tradução `{lang}` do CV v{active.versao}: "
            f"`{data['file_name']}`",
            parse_mode="Markdown",
        )
        log.info(
            "cv_upload_as_translation",
            cv_id=active.id,
            lang=lang,
            path=str(dest),
        )
        return


cv_upload_callback_handler = CallbackQueryHandler(
    cv_upload_callback, pattern=r"^cv:(new|tr|cancel)(:[a-z]{2})?:[\w-]+$"
)


@admin_only
async def cv_status_handler(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    maker = get_session_maker()
    async with maker() as session:
        cv = await get_active_cv(session)
        if cv is None:
            await update.message.reply_text(
                "Nenhum CV ativo ainda. Envie um PDF com /upload_cv."
            )
            return
        total_chunks = (
            await session.execute(
                select(func.count()).select_from(CVChunk).where(CVChunk.cv_id == cv.id)
            )
        ).scalar_one()
        await update.message.reply_text(
            f"CV ativo: versão {cv.versao}, {total_chunks} chunks "
            f"(adicionado em {cv.criada_em:%Y-%m-%d %H:%M})."
        )
