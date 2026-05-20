"""Load .env and Streamlit secrets into the shared config cache."""

from frontend.utils.config_loader import apply_streamlit_secrets_to_environ

__all__ = ["apply_streamlit_secrets_to_environ"]
