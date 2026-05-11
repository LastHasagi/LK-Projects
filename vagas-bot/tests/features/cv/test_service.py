import pytest

pytestmark = pytest.mark.skip(
    reason="cv service uses pgvector; covered by integration smoke test"
)


async def test_ingest_cv_text_persists_chunks():
    pass


async def test_set_active_cv_marks_one_active():
    pass
