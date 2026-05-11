from pathlib import Path

from arq.connections import ArqRedis, create_pool
from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.core.telegram import admin_only
from app.features.cv.models import CVChunk
from app.features.cv.service import get_active_cv

log = get_logger(__name__)

CV_DIR = Path("/app/data/cv")


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
    await msg.reply_text(f"Recebi. Indexando {doc.file_name}…")

    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("reindex_cv", str(dest))
    finally:
        await pool.close()


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
