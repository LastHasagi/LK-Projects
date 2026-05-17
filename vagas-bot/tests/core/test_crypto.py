from cryptography.fernet import Fernet

from app.core.crypto import decrypt, encrypt


def test_roundtrip(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("FERNET_KEY", key)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("TELEGRAM_ADMIN_USER_ID", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
    monkeypatch.setenv("REDIS_URL", "redis://r/0")

    # invalida cache do get_settings
    from app.core.config import get_settings
    get_settings.cache_clear()

    cipher = encrypt(b"segredo")
    assert cipher != b"segredo"
    assert decrypt(cipher) == b"segredo"
