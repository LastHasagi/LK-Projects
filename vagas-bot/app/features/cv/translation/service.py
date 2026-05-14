from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rag.chunker import parse_pdf
from app.features.cv.models import CV, CVTranslation
from app.features.cv.translation.renderer import render_markdown_to_pdf
from app.features.cv.translation.translator import translate_cv_to_markdown

SUPPORTED_LANGS = ("pt", "en", "es", "fr")
_OUTPUT_DIR = Path("data/cv_translations")


class CVTranslationError(Exception):
    pass


async def save_user_provided_translation(
    session: AsyncSession,
    *,
    cv_id: int,
    target_lang: str,
    pdf_path: str,
) -> CVTranslation:
    """Registra (ou atualiza) tradução do CV fornecida pelo próprio usuário,
    sem chamar LLM. Apenas extrai o texto do PDF e grava como markdown."""
    if target_lang not in SUPPORTED_LANGS:
        raise CVTranslationError(
            f"Idioma não suportado: {target_lang}. Use {', '.join(SUPPORTED_LANGS)}."
        )
    try:
        text = parse_pdf(pdf_path)
    except Exception as e:
        raise CVTranslationError(f"Falha ao ler PDF: {e!s}") from e
    if not text.strip():
        raise CVTranslationError("PDF sem texto extraível.")

    existing = (
        await session.execute(
            select(CVTranslation).where(
                CVTranslation.cv_id == cv_id, CVTranslation.lang == target_lang
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        row = CVTranslation(
            cv_id=cv_id,
            lang=target_lang,
            markdown_text=text,
            pdf_path=pdf_path,
        )
        session.add(row)
    else:
        existing.markdown_text = text
        existing.pdf_path = pdf_path
        row = existing
    await session.commit()
    await session.refresh(row)
    return row


async def get_or_create_translated_cv(
    session: AsyncSession, *, cv_id: int, target_lang: str
) -> CVTranslation:
    if target_lang not in SUPPORTED_LANGS:
        raise CVTranslationError(
            f"Idioma não suportado: {target_lang}. Use {', '.join(SUPPORTED_LANGS)}."
        )

    existing = (
        await session.execute(
            select(CVTranslation).where(
                CVTranslation.cv_id == cv_id, CVTranslation.lang == target_lang
            )
        )
    ).scalar_one_or_none()
    if existing is not None and Path(existing.pdf_path).exists():
        return existing

    cv = (
        await session.execute(select(CV).where(CV.id == cv_id))
    ).scalar_one_or_none()
    if cv is None:
        raise CVTranslationError(f"CV id={cv_id} não encontrado.")

    try:
        source_text = parse_pdf(cv.path_pdf)
    except Exception as e:
        raise CVTranslationError(f"Falha ao ler PDF original: {e!s}") from e
    if not source_text.strip():
        raise CVTranslationError("PDF do CV sem texto extraível.")

    try:
        markdown_text = await translate_cv_to_markdown(source_text, target_lang)
    except Exception as e:
        raise CVTranslationError(f"Falha na tradução LLM: {e!s}") from e

    output_path = _OUTPUT_DIR / f"{cv_id}_{target_lang}.pdf"
    try:
        render_markdown_to_pdf(markdown_text, output_path)
    except Exception as e:
        raise CVTranslationError(f"Falha ao gerar PDF: {e!s}") from e

    if existing is None:
        row = CVTranslation(
            cv_id=cv_id,
            lang=target_lang,
            markdown_text=markdown_text,
            pdf_path=str(output_path),
        )
        session.add(row)
    else:
        existing.markdown_text = markdown_text
        existing.pdf_path = str(output_path)
        row = existing
    await session.commit()
    await session.refresh(row)
    return row
