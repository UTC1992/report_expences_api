from functools import lru_cache
from urllib.parse import quote_plus

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

    db_host: str = Field(default="", description="PostgreSQL host")
    db_port: str = Field(default="", description="PostgreSQL port")
    db_name: str = Field(default="", description="PostgreSQL database name")
    db_user: str = Field(default="", description="PostgreSQL user")
    db_password: str = Field(default="", description="PostgreSQL password")
    database_url: str = Field(
        default="",
        description="Optional full URL; overrides composed DB fields when set",
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
        if self.database_url.strip():
            url = self.database_url.strip()
            if url.startswith("postgresql://") and "+asyncpg" not in url:
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        if not (self.db_host and self.db_name and self.db_user):
            return None
        port = self.db_port.strip() or "5432"
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        host = self.db_host.strip()
        name = self.db_name.strip()
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

    def resolve_sync_database_url(self) -> str | None:
        """Sync URL for Alembic (psycopg)."""
        if self.database_url.strip():
            u = self.database_url.strip()
            return u.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1).replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        if not (self.db_host and self.db_name and self.db_user):
            return None
        port = self.db_port.strip() or "5432"
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        host = self.db_host.strip()
        name = self.db_name.strip()
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"

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
