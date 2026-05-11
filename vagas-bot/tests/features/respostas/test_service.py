import pytest

pytestmark = pytest.mark.skip(
    reason="resposta_custom uses pgvector; covered by integration smoke test"
)


async def test_upsert_then_buscar_match_semantic():
    pass


async def test_buscar_retorna_none_abaixo_do_threshold():
    pass
