"""Resolve config from .env, os.environ, and st.secrets (Streamlit Cloud)."""

import os
from functools import lru_cache
from typing import Any, Optional


def _clean(value: Optional[str]) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    return s


def _flatten_secrets(prefix: str, value: Any, out: dict[str, str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            part = str(k).strip().upper()
            child = f"{prefix}_{part}" if prefix else part
            _flatten_secrets(child, v, out)
    elif isinstance(value, bool):
        out[prefix] = "true" if value else "false"
    elif isinstance(value, (str, int, float)):
        out[prefix] = _clean(str(value))


@lru_cache(maxsize=1)
def load_config() -> dict[str, str]:
    """Merge dotenv, environment variables, and Streamlit secrets (cached per process)."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    cfg: dict[str, str] = {}
    for k, v in os.environ.items():
        cv = _clean(v)
        if cv:
            cfg[k.upper()] = cv

    try:
        import streamlit as st

        flat: dict[str, str] = {}
        _flatten_secrets("", dict(st.secrets), flat)
        for k, v in flat.items():
            if v:
                cfg.setdefault(k, v)
    except Exception:
        pass

    return cfg


def get_config(*keys: str) -> str:
    cfg = load_config()
    for k in keys:
        v = cfg.get(k.upper())
        if v:
            return v
    return ""


def list_config_keys() -> list[str]:
    return sorted(load_config().keys())


def apply_streamlit_secrets_to_environ() -> None:
    """Copy merged config into os.environ for libraries that only read env vars."""
    for k, v in load_config().items():
        if v and not _clean(os.environ.get(k)):
            os.environ[k] = v
