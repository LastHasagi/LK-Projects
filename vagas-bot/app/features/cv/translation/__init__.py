from app.features.cv.translation.service import (
    SUPPORTED_LANGS,
    CVTranslationError,
    get_or_create_translated_cv,
)

__all__ = [
    "SUPPORTED_LANGS",
    "CVTranslationError",
    "get_or_create_translated_cv",
]
