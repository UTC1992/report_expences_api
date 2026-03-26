from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Personal Expenses API"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = Field(
        default="*",
        description="Comma-separated origins for Flutter/web clients",
    )
    persistence_provider: str = Field(
        default="memory",
        description="memory | postgres",
    )
    llm_provider: str = Field(
        default="openai_stub",
        description="openai_stub | openai (future)",
    )
    openai_api_key: str | None = Field(default=None, description="Optional; required for real OpenAI calls")
    log_level: str = Field(default="INFO", description="DEBUG | INFO | WARNING | ERROR")

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
