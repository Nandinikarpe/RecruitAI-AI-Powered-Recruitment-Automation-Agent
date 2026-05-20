"""Load .env then Streamlit Cloud secrets into os.environ (supports nested [supabase] sections)."""

import os


def _flatten_to_env(prefix: str, value, out: dict[str, str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            part = str(k).strip().upper()
            child_prefix = f"{prefix}_{part}" if prefix else part
            _flatten_to_env(child_prefix, v, out)
    elif isinstance(value, bool):
        out[prefix] = "true" if value else "false"
    elif isinstance(value, (str, int, float)):
        out[prefix] = str(value).strip()


def apply_streamlit_secrets_to_environ() -> None:
    """Call once at app startup (after `import streamlit`). Safe on local runs without secrets."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    try:
        import streamlit as st

        flat: dict[str, str] = {}
        _flatten_to_env("", dict(st.secrets), flat)
        for k, v in flat.items():
            if v and k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass
