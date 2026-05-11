from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import get_settings

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIMS = 1536


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    resp = await _get_client().embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]
