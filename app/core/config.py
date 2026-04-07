from functools import lru_cache

from pydantic import Field, field_validator
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
    cors_origins: str = Field(default="*", description="Comma-separated origins")

    persistence_provider: str = Field(
        default="memory",
        description="memory | postgres",
    )

    database_url: str = Field(
        default="",
        description="PostgreSQL URL (single source of truth for host, port, db, credentials)",
    )

    openai_api_key: str = Field(default="", description="Optional server fallback OpenAI key")
    openai_model: str = Field(default="", description="Default model; empty uses gpt-4o-mini")

    log_level: str = Field(default="INFO", description="DEBUG | INFO | WARNING | ERROR")

    @field_validator("app_name", mode="before")
    @classmethod
    def _default_app_name(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return "Personal Expenses API"
        return str(v)

    @field_validator("api_prefix", mode="before")
    @classmethod
    def _default_api_prefix(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return "/api/v1"
        return str(v)

    @field_validator("persistence_provider", mode="before")
    @classmethod
    def _default_persistence(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return "memory"
        return str(v).strip().lower()

    def resolve_async_database_url(self) -> str | None:
        if not self.database_url.strip():
            return None
        url = self.database_url.strip()
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    def resolve_sync_database_url(self) -> str | None:
        """Sync URL for Alembic (psycopg)."""
        if not self.database_url.strip():
            return None
        u = self.database_url.strip()
        return u.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1).replace(
            "postgresql://", "postgresql+psycopg://", 1
        )

    def resolve_openai_model(self) -> str:
        return self.openai_model.strip() or "gpt-4o-mini"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
