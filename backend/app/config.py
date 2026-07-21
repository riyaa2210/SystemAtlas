"""
Application configuration using pydantic-settings.
All values are read from environment variables / .env file.
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
    app_env: str = "development"
    app_name: str = "Living Architecture Map"
    app_version: str = "1.0.0"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lam_db"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # JWT — default only safe for dev; always override in production
    secret_key: str = "dev-secret-key-change-this-in-production-32chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # AI
    gemini_api_key: str = ""

    # GitHub
    github_token: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"

    # Temp directory for cloned repos
    temp_dir: str = "/tmp/lam-scans"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()
