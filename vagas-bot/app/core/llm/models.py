from typing import Literal

Role = Literal["FAST", "SMART"]

PROVIDER_MODELS: dict[str, dict[Role, str]] = {
    "openai": {
        "FAST": "gpt-5-mini",
        "SMART": "gpt-5",
    },
    "anthropic": {
        "FAST": "claude-haiku-4-5-20251001",
        "SMART": "claude-sonnet-4-6",
    },
}
