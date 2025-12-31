"""Application configuration settings."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+18+for+SQL+Server"

    # Security
    secret_key: str = "change-me-in-production"
    encryption_key: str = "change-me-32-byte-base64-key-here"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Trial settings
    trial_duration_days: int = 14

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
