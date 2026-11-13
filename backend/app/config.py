from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./demo.db"
    cors_origins: str = "http://localhost:5173"

    # Auth
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 60 * 12

    # LLM: "auto" uses Anthropic when ANTHROPIC_API_KEY is set, otherwise the fake provider.
    llm_provider: str = "auto"  # auto | fake | anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    fake_token_delay_ms: int = 0

    # Gateway limits
    rate_limit_per_minute: int = 10
    max_code_chars: int = 20_000


@lru_cache
def get_settings() -> Settings:
    return Settings()
