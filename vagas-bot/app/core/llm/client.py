from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.llm.models import PROVIDER_MODELS, Role


@lru_cache(maxsize=4)
def get_llm(role: Role = "FAST") -> BaseChatModel:
    settings = get_settings()
    provider = settings.llm_provider
    if provider not in PROVIDER_MODELS:
        raise ValueError(f"Provider not supported: {provider}")
    model_name = PROVIDER_MODELS[provider][role]
    if provider == "openai":
        return ChatOpenAI(model=model_name, api_key=settings.openai_api_key, temperature=0)
    raise NotImplementedError(f"Provider {provider} requires langchain-{provider} install")
