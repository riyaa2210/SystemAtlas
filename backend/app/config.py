"""
Application configuration using pydantic-settings.
All fields have production-safe defaults so Render works without env vars.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "production"
    app_name: str = "Living Architecture Map"
    app_version: str = "1.0.0"

    # PostgreSQL — Supabase Session Pooler (port 5432, statement_cache_size=0)
    database_url: str = (
        "postgresql+asyncpg://postgres.vgwenhmvnjtfhkyuskib:Riya2211Rps"
        "@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
    )

    # Neo4j — optional, graph features skip gracefully if unavailable
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # JWT
    secret_key: str = "3ce8f78a3bc9a55ef35c52d8614df5bd9d84b3b3e1c76fd7b2b2e6af3e7ab419"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # AI — Gemini API key
    gemini_api_key: str = ""

    # GitHub
    github_token: str = ""

    # CORS — includes all deployment URLs
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "http://localhost:5173,"
        "https://systematlas-1.onrender.com,"
        "https://systematlas.onrender.com"
    )

    # Temp directory
    temp_dir: str = "/tmp/lam-scans"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
