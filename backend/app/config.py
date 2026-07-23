"""
Application configuration using pydantic-settings.
All values are read from environment variables / .env file.
All fields have safe defaults so startup never crashes from missing vars.
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

    # PostgreSQL — default is local dev; set DATABASE_URL env var in production
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/lam_db"

    # Neo4j — optional; graph features degrade gracefully if unavailable
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "password"

    # JWT
    secret_key: str = "dev-secret-key-change-in-production-minimum-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # AI — optional; copilot disabled if empty
    gemini_api_key: str = ""

    # GitHub — optional; lower rate limit without token
    github_token: str = ""

    # CORS — comma-separated list of allowed origins
    # Production: set CORS_ORIGINS env var in Render to include your Vercel URL
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
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached settings — loaded once at startup."""
    return Settings()
