import os

import pytest

from app.core.config import Settings


def _env(monkeypatch, **values):
    for k, v in values.items():
        monkeypatch.setenv(k, v)


def test_settings_loads_required_fields(monkeypatch):
    _env(
        monkeypatch,
        TELEGRAM_BOT_TOKEN="abc",
        TELEGRAM_ADMIN_USER_ID="42",
        OPENAI_API_KEY="sk-x",
        DATABASE_URL="postgresql+asyncpg://u:p@h/db",
        REDIS_URL="redis://r:6379/0",
        FERNET_KEY="key",
    )
    s = Settings()
    assert s.telegram_bot_token == "abc"
    assert s.telegram_admin_user_id == 42
    assert s.database_url == "postgresql+asyncpg://u:p@h/db"
    assert s.log_level == "INFO"  # default
    assert s.env == "dev"  # default
    assert s.smtp_user is None
    assert s.smtp_host == "smtp.gmail.com"
    assert s.smtp_port == 587


def test_settings_missing_required_raises(monkeypatch):
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ADMIN_USER_ID", "OPENAI_API_KEY",
              "DATABASE_URL", "REDIS_URL", "FERNET_KEY"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(Exception):
        Settings()
