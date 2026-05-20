import os
from functools import lru_cache

from pydantic_settings import BaseSettings

_SECRET_KEYS = (
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "HR_EMAIL",
    "COMPANY_NAME",
)


def _apply_streamlit_secrets() -> None:
    try:
        import streamlit as st

        for key in _SECRET_KEYS:
            if key in st.secrets and not os.environ.get(key):
                os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    hr_email: str = ""
    company_name: str = "Recruitment Team"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    _apply_streamlit_secrets()
    return Settings()
