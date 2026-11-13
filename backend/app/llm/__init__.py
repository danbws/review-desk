from app.config import Settings
from app.llm.base import LLMProvider, ProviderError
from app.llm.fake import FakeProvider

__all__ = ["LLMProvider", "ProviderError", "build_provider"]


def build_provider(settings: Settings) -> LLMProvider:
    choice = settings.llm_provider
    if choice == "auto":
        choice = "anthropic" if settings.anthropic_api_key else "fake"
    if choice == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
        from app.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    return FakeProvider(settings.fake_token_delay_ms)
