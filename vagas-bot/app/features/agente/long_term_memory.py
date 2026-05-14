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
    """Busca semântica no namespace ("user_facts", admin_id, *) em UMA query."""
    admin_id = str(get_settings().telegram_admin_user_id)
    results = await store.asearch(("user_facts", admin_id), query=query, limit=k)
    return [
        {
            "key": item.key,
            "categoria": (item.namespace[-1] if item.namespace else ""),
            "fato": (item.value or {}).get("fato", ""),
            "score": getattr(item, "score", None),
        }
        for item in results
    ]


async def list_all_facts(store: BaseStore) -> list[dict]:
    """Lista todos os fatos (sem ranking semântico) — usado para pré-injeção barata."""
    admin_id = str(get_settings().telegram_admin_user_id)
    results = await store.asearch(("user_facts", admin_id), query="", limit=50)
    return [
        {
            "categoria": (item.namespace[-1] if item.namespace else ""),
            "fato": (item.value or {}).get("fato", ""),
        }
        for item in results
        if (item.value or {}).get("fato")
    ]
