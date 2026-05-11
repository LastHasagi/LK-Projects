from typing import Literal

Role = Literal["FAST", "SMART"]

PROVIDER_MODELS: dict[str, dict[Role, str]] = {
    "openai": {
        "FAST": "gpt-4o-mini",
        "SMART": "gpt-4o",
    },
    "anthropic": {
        "FAST": "claude-haiku-4-5-20251001",
        "SMART": "claude-sonnet-4-6",
    },
}
