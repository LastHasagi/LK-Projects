import json
import logging

import pytest

from app.core.logging import configure_logging, get_logger, redact_secrets


def test_redact_secrets_masks_known_keys():
    payload = {
        "msg": "ok",
        "authorization": "Bearer xyz",
        "cookie": "abc=1",
        "fernet_key": "sensitive",
        "user_id": 42,
    }
    redacted = redact_secrets(None, None, dict(payload))
    assert redacted["authorization"] == "***"
    assert redacted["cookie"] == "***"
    assert redacted["fernet_key"] == "***"
    assert redacted["user_id"] == 42


def test_configure_logging_emits_json(capsys):
    configure_logging(level="INFO")
    log = get_logger("test")
    log.info("hello", chat_id=42)
    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    obj = json.loads(line)
    assert obj["event"] == "hello"
    assert obj["chat_id"] == 42
    assert obj["level"] == "info"
