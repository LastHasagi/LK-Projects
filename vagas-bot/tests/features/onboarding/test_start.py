from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.features.onboarding.handlers import start_handler


@pytest.mark.asyncio
async def test_start_replies_welcome():
    user = SimpleNamespace(id=100, first_name="Rod", username="rod")
    message = SimpleNamespace(reply_text=AsyncMock())
    update = SimpleNamespace(effective_user=user, effective_message=message, message=message)
    context = SimpleNamespace()

    await start_handler(update, context)

    message.reply_text.assert_awaited_once()
    text = message.reply_text.await_args.args[0]
    assert "Olá" in text or "Bem-vindo" in text


@pytest.mark.asyncio
async def test_start_rejects_non_admin():
    user = SimpleNamespace(id=999, first_name="x", username="x")
    message = SimpleNamespace(reply_text=AsyncMock())
    update = SimpleNamespace(effective_user=user, effective_message=message, message=message)

    await start_handler(update, SimpleNamespace())

    text = message.reply_text.await_args.args[0]
    assert "autoriz" in text.lower()
