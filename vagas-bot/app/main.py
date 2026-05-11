import asyncio
import contextlib

import uvicorn
from telegram.ext import CommandHandler, MessageHandler, filters

from app.core.api import create_api
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.telegram import build_application
from app.features.admin.handlers import admin_callback_handler, admin_handler
from app.features.agente.graph import graph_lifespan
from app.features.agente.handlers import conversational_message_handler
from app.features.candidatura.handlers import (
    candidatura_cancelar_handler,
    vaga_candidatar_handler,
    vagas_command,
)
from app.features.cv.handlers import cv_status_handler, upload_cv_handler
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


async def main() -> None:
    settings = get_settings()
    configure_logging(level=settings.log_level)
    log = get_logger(__name__)
    log.info("bot_starting", env=settings.env)

    api = create_api()
    application = build_application()
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("relogin", relogin_handler))
    application.add_handler(CommandHandler("cv", cv_status_handler))
    application.add_handler(CommandHandler("respostas", respostas_handler))
    application.add_handler(respostas_del_handler)
    application.add_handler(MessageHandler(filters.Document.PDF, upload_cv_handler))
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
    application.add_handler(conversational_message_handler)

    api_task = asyncio.create_task(_run_uvicorn(api))

    async with graph_lifespan():
        async with application:
            await application.start()
            await application.updater.start_polling()
            try:
                await api_task
            finally:
                await application.updater.stop()
                await application.stop()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
