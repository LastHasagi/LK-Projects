import pytest

pytestmark = pytest.mark.skip(
    reason="vaga uses pgvector; covered by integration smoke test"
)


async def test_dedupe_by_url():
    pass


async def test_dedupe_by_semantic_similarity():
    pass


async def test_persist_with_filtro():
    pass
