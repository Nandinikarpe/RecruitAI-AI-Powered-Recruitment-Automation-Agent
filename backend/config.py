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

    supabase_url: str = Field(
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_key: str = Field(
        validation_alias=AliasChoices(
            "SUPABASE_KEY",
            "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        ),
    )
    # Optional: if empty, admin routes use the same client as `supabase_key` (fine when RLS is off).
    supabase_service_key: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_SERVICE_KEY", "SUPABASE_SECRET_KEY"),
    )

    gemini_api_key: str = Field(validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"))
    # Free-tier friendly default; override with e.g. `gemini-2.0-flash` if your SDK supports it.
    gemini_model: str = Field(default="gemini-1.5-flash", validation_alias=AliasChoices("GEMINI_MODEL"))

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    gmail_user: str
    gmail_app_password: str
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:8501"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
