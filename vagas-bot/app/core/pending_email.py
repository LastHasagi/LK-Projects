import json
import uuid
from typing import Any

from app.core.redis import get_redis

_PREFIX = "vagas:pending_email:"
_TTL_SEC = 15 * 60

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


async def pend_email_delete(uid: str) -> None:
    """Remove o rascunho."""
    r = get_redis()
    await r.delete(_PREFIX + uid)
