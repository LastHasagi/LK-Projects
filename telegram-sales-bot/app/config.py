from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
from functools import lru_cache


class Settings(BaseSettings):
    # Bot Configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    telegram_webhook_url: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field("HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Payment Gateways
    mercadopago_access_token: Optional[str] = Field(None, env="MERCADOPAGO_ACCESS_TOKEN")
    mercadopago_public_key: Optional[str] = Field(None, env="MERCADOPAGO_PUBLIC_KEY")
    mercadopago_webhook_secret: Optional[str] = Field(None, env="MERCADOPAGO_WEBHOOK_SECRET")
    
    stripe_secret_key: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    stripe_publishable_key: Optional[str] = Field(None, env="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET")
    
    # Application
    app_name: str = Field("Telegram Sales Bot", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    
    # Admin
    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field(..., env="ADMIN_PASSWORD")
    
    # Telegram Groups
    default_invite_link_expiry_hours: int = Field(24, env="DEFAULT_INVITE_LINK_EXPIRY_HOURS")
    
    # Upload settings
    upload_folder: str = "static/uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: set = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create upload folder if it doesn't exist (only if settings are available)
try:
    settings = get_settings()
    os.makedirs(settings.upload_folder, exist_ok=True)
except:
    # Settings not available yet (e.g., during setup)
    pass
