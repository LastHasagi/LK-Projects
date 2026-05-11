from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text


async def ping_db() -> bool:
    try:
        from app.core.db import get_session_maker
        async with get_session_maker()() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def ping_redis() -> bool:
    try:
        from app.core.redis import get_redis
        client = get_redis()
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


def create_api() -> FastAPI:
    app = FastAPI(title="vagas-bot")

    @app.get("/healthz")
    async def healthz():
        db_ok = await ping_db()
        redis_ok = await ping_redis()
        body = {
            "status": "ok" if (db_ok and redis_ok) else "degraded",
            "db": "ok" if db_ok else "fail",
            "redis": "ok" if redis_ok else "fail",
        }
        code = 200 if (db_ok and redis_ok) else 503
        return JSONResponse(body, status_code=code)

    return app
