import asyncio
import contextlib
import os

import uvicorn
from telegram.ext import CommandHandler, MessageHandler, filters

from app.core.api import create_api
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.telegram import build_application
from app.features.admin.handlers import admin_callback_handler, admin_handler
from app.features.agente.email_handlers import email_inline_handler
from app.features.agente.graph import graph_lifespan
from app.features.agente.handlers import conversational_message_handler
from app.features.agente.photo_handler import photo_message_handler_instance
from app.features.agente.reset_handler import reset_thread_command
from app.features.candidatura.handlers import (
    candidatura_cancelar_handler,
    vaga_candidatar_handler,
    vagas_command,
)
from app.features.cv.handlers import (
    cv_status_handler,
    cv_upload_callback_handler,
    upload_cv_handler,
)
from app.features.email_submission.handlers import vagas_email_command
from app.features.descoberta.handlers import (
    insta_search_handler,
    link_drop_message_handler,
    vaga_ignorar_handler,
)
from app.features.filtros.handlers import (
    filtros_add_conversation,
    filtros_handler,
    filtros_off_handler,
)
from app.features.onboarding.handlers import start_handler
from app.features.respostas.handlers import respostas_del_handler, respostas_handler
from app.features.sessao_gupy.handlers import relogin_handler


async def _run_uvicorn(app):
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()


async def _polling_supervisor(application, log) -> None:
    """Mantém o long-polling vivo. Em caso de crash transitório (NetworkError,
    ConnectError, DNS), aguarda backoff e reinicia o updater. Aborta apenas se
    o erro persistir após muitas tentativas (provavelmente token revogado)."""
    consecutive_failures = 0
    while True:
        try:
            await application.updater.start_polling()
            consecutive_failures = 0
            log.info("polling_started")
            while application.updater.running:
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            consecutive_failures += 1
            backoff = min(60, 2 ** min(consecutive_failures, 6))
            log.warning(
                "polling_crashed",
                error=str(e),
                attempt=consecutive_failures,
                backoff_s=backoff,
            )
            try:
                if application.updater.running:
                    await application.updater.stop()
            except Exception:
                pass
            if consecutive_failures >= 15:
                log.error("polling_giving_up", failures=consecutive_failures)
                raise
            await asyncio.sleep(backoff)


async def main() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    log = get_logger(__name__)
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        log.info("langsmith_enabled", project=settings.langchain_project)
    log.info("bot_starting", env=settings.env)

    api = create_api()
    application = build_application()
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("relogin", relogin_handler))
    application.add_handler(CommandHandler("cv", cv_status_handler))
    application.add_handler(CommandHandler("respostas", respostas_handler))
    application.add_handler(respostas_del_handler)
    application.add_handler(MessageHandler(filters.Document.PDF, upload_cv_handler))
    application.add_handler(cv_upload_callback_handler)
    application.add_handler(CommandHandler("filtros", filtros_handler))
    application.add_handler(filtros_add_conversation)
    application.add_handler(filtros_off_handler)
    application.add_handler(CommandHandler("insta_search", insta_search_handler))
    application.add_handler(link_drop_message_handler)
    application.add_handler(vaga_ignorar_handler)
    application.add_handler(CommandHandler("vagas", vagas_command))
    application.add_handler(vaga_candidatar_handler)
    application.add_handler(candidatura_cancelar_handler)
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(admin_callback_handler)
    application.add_handler(reset_thread_command)
    application.add_handler(vagas_email_command)
    application.add_handler(email_inline_handler)
    application.add_handler(photo_message_handler_instance)
    application.add_handler(conversational_message_handler)

    api_task = asyncio.create_task(_run_uvicorn(api))

    async with graph_lifespan():
        async with application:
            await application.start()
            polling_task = asyncio.create_task(
                _polling_supervisor(application, log)
            )
            try:
                done, _ = await asyncio.wait(
                    [api_task, polling_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for t in done:
                    exc = t.exception()
                    if exc is not None:
                        raise exc
            finally:
                for t in (polling_task, api_task):
                    if not t.done():
                        t.cancel()
                with contextlib.suppress(BaseException):
                    await asyncio.gather(polling_task, api_task, return_exceptions=True)
                try:
                    if application.updater.running:
                        await application.updater.stop()
                except Exception:
                    pass
                await application.stop()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
