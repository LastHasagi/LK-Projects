import json
import uuid
from typing import Any

from app.core.redis import get_redis

_PREFIX = "vagas:pending_email:"
_TTL_SEC = 4 * 60 * 60
_REVISION_PREFIX = "vagas:email_revision:"
_REVISION_TTL_SEC = 15 * 60

EMAIL_CONFIRM_PENDING_PREFIX = "EMAIL_CONFIRM_PENDING:"


async def pend_email_save(payload: dict[str, Any]) -> str:
    """Grava rascunho de e-mail no Redis e devolve o id usado nos callback_data."""
    uid = str(uuid.uuid4())
    r = get_redis()
    await r.setex(_PREFIX + uid, _TTL_SEC, json.dumps(payload, ensure_ascii=False))
    return uid


async def pend_email_get(uid: str) -> dict[str, Any] | None:
    """Lê o rascunho sem remover."""
    r = get_redis()
    raw = await r.get(_PREFIX + uid)
    if raw is None:
        return None
    return json.loads(raw)


async def pend_email_save_existing(uid: str, payload: dict[str, Any]) -> None:
    """Reescreve o payload de um uid já existente (preserva TTL aproximado)."""
    r = get_redis()
    await r.setex(_PREFIX + uid, _TTL_SEC, json.dumps(payload, ensure_ascii=False))


async def pend_email_delete(uid: str) -> None:
    """Remove o rascunho."""
    r = get_redis()
    await r.delete(_PREFIX + uid)


async def revision_set(chat_id: int) -> None:
    """Marca que o chat está em fluxo de revisão de rascunho."""
    r = get_redis()
    await r.setex(_REVISION_PREFIX + str(chat_id), _REVISION_TTL_SEC, "1")


async def revision_active(chat_id: int) -> bool:
    r = get_redis()
    val = await r.get(_REVISION_PREFIX + str(chat_id))
    return val is not None


async def revision_clear(chat_id: int) -> None:
    r = get_redis()
    await r.delete(_REVISION_PREFIX + str(chat_id))
