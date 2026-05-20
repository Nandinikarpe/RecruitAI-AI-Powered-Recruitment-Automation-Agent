"""Where the FastAPI backend lives. Streamlit Cloud cannot use localhost — set BACKEND_URL."""

import os

_dotenv_loaded = False


def _load_dotenv_once() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def get_backend_url() -> str:
    """
    Resolution order:
    1. BACKEND_URL or STREAMLIT_BACKEND_URL or API_URL (environment)
    2. Same keys in Streamlit secrets (Community Cloud dashboard)
    3. http://localhost:8000
    """
    _load_dotenv_once()
    for key in ("BACKEND_URL", "STREAMLIT_BACKEND_URL", "API_URL"):
        v = (os.environ.get(key) or "").strip().rstrip("/")
        if v:
            return v
    try:
        import streamlit as st

        if hasattr(st, "secrets"):
            for sk in ("BACKEND_URL", "API_URL"):
                if sk in st.secrets:
                    v = str(st.secrets[sk]).strip().rstrip("/")
                    if v:
                        return v
    except Exception:
        pass
    return "http://localhost:8000"
