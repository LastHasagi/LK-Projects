import logging
import sys

import structlog

SECRET_KEYS = {"authorization", "cookie", "cookies", "fernet_key", "openai_api_key",
               "telegram_bot_token", "anthropic_api_key", "password", "token"}

NOISY_LIBRARY_LOGGERS = ("httpx", "httpcore", "telegram", "asyncio", "uvicorn.access")


def redact_secrets(_logger, _name, event_dict: dict) -> dict:
    for key in list(event_dict.keys()):
        if key.lower() in SECRET_KEYS:
            event_dict[key] = "***"
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )
    for name in NOISY_LIBRARY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            redact_secrets,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
