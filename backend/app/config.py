from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "production"
    app_name: str = "Living Architecture Map"
    app_version: str = "1.0.0"

    # Database
    database_url: str = ""

    # Neo4j
    neo4j_uri: str = ""
    neo4j_username: str = ""
    neo4j_password: str = ""

    # JWT
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Gemini
    gemini_api_key: str = ""

    # GitHub
    github_token: str = ""

    # CORS
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:3001,"
        "http://localhost:5173,"
        "https://systematlas-1.onrender.com,"
        "https://systematlas.onrender.com"
    )

    temp_dir: str = "/tmp/lam-scans"

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_development(self):
        return self.app_env == "development"


@lru_cache
def get_settings():
    return Settings()