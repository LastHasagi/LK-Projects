from typing import Literal

from langgraph.store.base import BaseStore

from app.core.config import get_settings

FactCategory = Literal["candidato", "compensacao_disponibilidade"]
ALLOWED_CATEGORIES: tuple[FactCategory, ...] = ("candidato", "compensacao_disponibilidade")


def _ns(categoria: FactCategory) -> tuple[str, ...]:
    return ("user_facts", str(get_settings().telegram_admin_user_id), categoria)


async def put_fact(
    store: BaseStore, *, key: str, fato: str, categoria: FactCategory
) -> None:
    await store.aput(_ns(categoria), key, {"fato": fato, "categoria": categoria})


async def search_facts(
    store: BaseStore, *, query: str, k: int = 5
) -> list[dict]:
    admin_id = str(get_settings().telegram_admin_user_id)
    hits = []
    for categoria in ALLOWED_CATEGORIES:
        ns = ("user_facts", admin_id, categoria)
        results = await store.asearch(ns, query=query, limit=k)
        for item in results:
            hits.append(
                {
                    "key": item.key,
                    "categoria": categoria,
                    "fato": (item.value or {}).get("fato", ""),
                    "score": getattr(item, "score", None),
                }
            )
    hits.sort(key=lambda h: (h["score"] is None, -(h["score"] or 0.0)))
    return hits[:k]
