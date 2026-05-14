from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    telegram_bot_token: str
    telegram_admin_user_id: int
    llm_provider: Literal["openai", "anthropic"] = "openai"
    openai_api_key: str
    database_url: str
    redis_url: str
    fernet_key: str
    log_level: str = "INFO"
    env: Literal["dev", "prod"] = "dev"
    daily_apply_limit: int = 20
    # SMTP opcional (ex.: Gmail + senha de app) para candidatura por e-mail
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_name: str | None = None
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "vagas-bot"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
