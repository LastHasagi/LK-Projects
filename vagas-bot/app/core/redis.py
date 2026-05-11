from functools import lru_cache

from arq.connections import RedisSettings
from redis.asyncio import Redis

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


def get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)
