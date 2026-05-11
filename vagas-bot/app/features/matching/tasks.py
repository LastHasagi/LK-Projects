from arq.connections import ArqRedis, create_pool

from app.core.db import get_session_maker
from app.core.logging import get_logger
from app.core.redis import get_redis_settings
from app.features.matching.service import match_scoring

log = get_logger(__name__)


async def match_score(ctx: dict, vaga_id: int, chat_id: int | None = None) -> int | None:
    maker = get_session_maker()
    async with maker() as session:
        result = await match_scoring(session, vaga_id)
    pool: ArqRedis = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job("notify_vaga", vaga_id, chat_id)
    finally:
        await pool.close()
    return result.id if result else None
