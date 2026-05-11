from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.features.cv.service import ingest_cv_from_pdf, set_active_cv

log = get_logger(__name__)


async def reindex_cv(ctx: dict, pdf_path: str) -> int:
    log.info("reindex_cv_started", pdf_path=pdf_path)
    maker = get_session_maker()
    async with maker() as session:
        cv = await ingest_cv_from_pdf(session, pdf_path=pdf_path)
        await set_active_cv(session, cv.id)
    log.info("reindex_cv_done", cv_id=cv.id, versao=cv.versao)
    return cv.id
