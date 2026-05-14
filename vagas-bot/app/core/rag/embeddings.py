from collections import OrderedDict
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import get_settings

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIMS = 1536

_CACHE_MAX = 512
_cache: "OrderedDict[str, list[float]]" = OrderedDict()


@lru_cache(maxsize=1)
def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)


def _cache_get(text: str) -> list[float] | None:
    if text in _cache:
        _cache.move_to_end(text)
        return _cache[text]
    return None


def _cache_put(text: str, emb: list[float]) -> None:
    _cache[text] = emb
    _cache.move_to_end(text)
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    out: list[list[float] | None] = [_cache_get(t) for t in texts]
    miss_idx = [i for i, v in enumerate(out) if v is None]
    if miss_idx:
        missing = [texts[i] for i in miss_idx]
        resp = await _get_client().embeddings.create(
            model=EMBED_MODEL, input=missing
        )
        for idx, item in zip(miss_idx, resp.data, strict=True):
            emb = item.embedding
            out[idx] = emb
            _cache_put(texts[idx], emb)
    return [v for v in out if v is not None]
