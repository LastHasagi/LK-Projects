from arq import cron
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.redis import get_redis_settings
from app.features.cv.tasks import reindex_cv
from app.features.descoberta.notifier import notify_vaga
from app.features.descoberta.tasks import scrape_all_due, scrape_job, scrape_search
from app.features.candidatura.notifier import (
    notify_candidatura_aplicada,
    notify_candidatura_falhou,
    notify_pergunta_pendente,
)
from app.features.candidatura.tasks import apply_job
from app.features.matching.tasks import match_score


async def startup(ctx: dict) -> None:
    configure_logging(level=get_settings().log_level)
    log = get_logger("worker")
    log.info("worker_started")
    ctx["log"] = log


async def shutdown(ctx: dict) -> None:
    log = ctx.get("log")
    if log:
        log.info("worker_stopped")


async def _heartbeat(ctx: dict) -> str:
    return "ok"


class WorkerSettings:
    redis_settings: RedisSettings = get_redis_settings()
    functions = [
        _heartbeat, reindex_cv,
        scrape_all_due, scrape_search, scrape_job,
        match_score, notify_vaga,
        apply_job, notify_pergunta_pendente, notify_candidatura_aplicada, notify_candidatura_falhou,
    ]
    cron_jobs = [
        cron(scrape_all_due, minute={0, 15, 30, 45}),
    ]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 4
