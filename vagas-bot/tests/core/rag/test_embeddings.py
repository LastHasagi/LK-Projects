from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.rag.embeddings import EMBED_DIMS, embed_texts


@pytest.mark.asyncio
async def test_embed_texts_returns_vectors():
    fake_resp = MagicMock()
    fake_resp.data = [
        MagicMock(embedding=[0.1] * EMBED_DIMS),
        MagicMock(embedding=[0.2] * EMBED_DIMS),
    ]
    with patch("app.core.rag.embeddings._get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.embeddings.create = AsyncMock(return_value=fake_resp)
        mock_get.return_value = mock_client
        result = await embed_texts(["a", "b"])
    assert len(result) == 2
    assert len(result[0]) == EMBED_DIMS
    assert result[0][0] == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_embed_texts_empty_returns_empty():
    result = await embed_texts([])
    assert result == []
