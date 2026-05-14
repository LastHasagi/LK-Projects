import json
import uuid
from typing import Any

from app.core.redis import get_redis

_PREFIX = "vagas:pending_cv_upload:"
_TTL_SEC = 30 * 60


async def pend_cv_save(payload: dict[str, Any]) -> str:
    uid = str(uuid.uuid4())
    r = get_redis()
    await r.setex(_PREFIX + uid, _TTL_SEC, json.dumps(payload, ensure_ascii=False))
    return uid


async def pend_cv_get(uid: str) -> dict[str, Any] | None:
    r = get_redis()
    raw = await r.get(_PREFIX + uid)
    if raw is None:
        return None
    return json.loads(raw)


async def pend_cv_delete(uid: str) -> None:
    r = get_redis()
    await r.delete(_PREFIX + uid)
