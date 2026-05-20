from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads `.env` from the process working directory (run commands from `recruitment-agent/`)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    gemini_model: str = Field(default="gemini-1.5-flash", validation_alias=AliasChoices("GEMINI_MODEL"))

    secret_key: str = Field(default="change-me-in-production", validation_alias=AliasChoices("SECRET_KEY"))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    gmail_user: str = ""
    gmail_app_password: str = ""

    data_dir: str = Field(default="data", validation_alias=AliasChoices("DATA_DIR"))
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
