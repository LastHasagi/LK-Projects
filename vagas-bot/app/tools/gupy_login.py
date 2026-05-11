import asyncio
import json
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.browser.camoufox import open_context
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.features.sessao_gupy.service import save_storage_state

GUPY_URL = "https://portal.gupy.io/"


def _host_database_url() -> str:
    url = get_settings().database_url
    return url.replace("@postgres:", "@localhost:").replace("@redis:", "@localhost:")


async def main() -> int:
    configure_logging(level="INFO")
    log = get_logger("gupy_login")
    log.info("opening_camoufox", url=GUPY_URL)

    async with open_context(headless=False) as ctx:
        page = await ctx.new_page()
        await page.goto(GUPY_URL)
        print()
        print("=" * 60)
        print("Faça login manualmente no Gupy nesta janela.")
        print("Quando terminar e estiver dentro da sua conta, volte aqui")
        print("e tecle ENTER para capturar a sessão.")
        print("=" * 60)
        try:
            await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        except (EOFError, KeyboardInterrupt):
            log.warning("login_aborted")
            return 1

        storage = await ctx.storage_state()
        payload = json.dumps(storage).encode()
        log.info("captured_storage_state", bytes=len(payload))

    engine = create_async_engine(_host_database_url(), pool_pre_ping=True)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with maker() as session:
            await save_storage_state(session, payload, rotulo="default")
    finally:
        await engine.dispose()
    log.info("session_saved")
    print("Sessão salva. Pode fechar esta janela.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
