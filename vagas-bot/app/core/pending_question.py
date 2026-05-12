from app.core.redis import get_redis

_PREFIX = "vagas:pending_question:"
_TTL_SEC = 24 * 60 * 60


async def pend_question_save(message_id: int, candidatura_id: int) -> None:
    """Mapeia o message_id da notificação da pergunta -> candidatura, com TTL de 24h."""
    r = get_redis()
    await r.setex(_PREFIX + str(message_id), _TTL_SEC, str(candidatura_id))


async def pend_question_get(message_id: int) -> int | None:
    """Devolve a candidatura associada ao message_id, ou None se expirou/não existe."""
    r = get_redis()
    raw = await r.get(_PREFIX + str(message_id))
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


async def pend_question_delete(message_id: int) -> None:
    r = get_redis()
    await r.delete(_PREFIX + str(message_id))
