import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """Default env vars for tests; individual tests can override."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_ID", "100")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://vagas:vagas@localhost:5432/vagas")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    from app.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
