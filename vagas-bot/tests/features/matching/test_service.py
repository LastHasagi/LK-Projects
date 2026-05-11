import pytest

pytestmark = pytest.mark.skip(
    reason="matching uses pgvector + LLM; covered by integration smoke test"
)


async def test_match_score_persists():
    pass


async def test_match_score_skips_when_no_cv():
    pass
