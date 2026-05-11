from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.telegram import admin_only


@pytest.fixture
def update_factory():
    def make(user_id: int):
        user = SimpleNamespace(id=user_id, username="u")
        message = SimpleNamespace(reply_text=AsyncMock())
        return SimpleNamespace(effective_user=user, effective_message=message, message=message)
    return make


@pytest.fixture
def context():
    return SimpleNamespace()


async def test_admin_passes_through(update_factory, context):
    update = update_factory(user_id=100)  # admin do conftest
    inner = AsyncMock()
    wrapped = admin_only(inner)
    await wrapped(update, context)
    inner.assert_awaited_once_with(update, context)


async def test_non_admin_rejected(update_factory, context):
    update = update_factory(user_id=999)
    inner = AsyncMock()
    wrapped = admin_only(inner)
    await wrapped(update, context)
    inner.assert_not_called()
    update.message.reply_text.assert_awaited_once()
    args = update.message.reply_text.await_args.args[0]
    assert "autoriz" in args.lower()
