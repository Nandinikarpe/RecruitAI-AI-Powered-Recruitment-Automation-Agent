"""Supabase URL/key from environment (Streamlit secrets or .env). Shared by frontend direct auth."""

import os
import socket
from typing import Optional
from urllib.parse import urlparse


def _clean(value: Optional[str]) -> str:
    if not value:
        return ""
    s = str(value).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    return s


def _first_env(*keys: str) -> str:
    for k in keys:
        v = _clean(os.environ.get(k))
        if v:
            return v
    return ""


def normalize_supabase_url(raw: str) -> str:
    """
    Return https://REF.supabase.co (no trailing slash).
    Raises RuntimeError with actionable text when the value is missing or invalid.
    """
    u = _clean(raw)
    if not u:
        raise RuntimeError(
            "SUPABASE_URL is not set. In Streamlit Cloud → Secrets, add:\n"
            'SUPABASE_URL = "https://YOUR_REF.supabase.co"\n'
            "(Copy Project URL from Supabase → Project Settings → API.)"
        )
    lower = u.lower()
    if "your_" in lower or lower in ("localhost", "example.com"):
        raise RuntimeError(
            f"SUPABASE_URL is still a placeholder ({u!r}). Set your real project URL from "
            "Supabase → Project Settings → API (https://xxxx.supabase.co)."
        )
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    parsed = urlparse(u)
    host = (parsed.netloc or parsed.path.split("/")[0]).strip()
    if not host or "." not in host:
        raise RuntimeError(
            f"SUPABASE_URL is invalid ({raw!r}). Use https://YOUR_REF.supabase.co with no spaces."
        )
    if "supabase.co" not in host and "supabase.in" not in host:
        raise RuntimeError(
            f"SUPABASE_URL host {host!r} does not look like a Supabase project URL. "
            "Expected https://YOUR_REF.supabase.co"
        )
    try:
        socket.getaddrinfo(host, 443)
    except socket.gaierror:
        raise RuntimeError(
            f"Cannot resolve Supabase host {host!r} (DNS failed). Check SUPABASE_URL for typos, "
            "confirm the project exists and is not deleted/paused, and use the URL from "
            "Supabase → Project Settings → API exactly."
        ) from None
    return f"https://{host}".rstrip("/")


def get_supabase_project_url() -> str:
    raw = _first_env("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_PROJECT_URL")
    return normalize_supabase_url(raw)


def get_supabase_auth_key() -> str:
    """
    Key for create_client(). Order:
    1. Service role (bypasses RLS)
    2. Legacy anon JWT (eyJ...)
    3. SUPABASE_KEY only if it looks like a JWT
    """
    for k in ("SUPABASE_SERVICE_KEY", "SUPABASE_SECRET_KEY"):
        v = _clean(os.environ.get(k))
        if v:
            return v

    anon = _first_env("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY")
    generic = _first_env("SUPABASE_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "SUPABASE_ANON_KEY")

    if anon:
        return anon
    if generic.startswith("eyJ"):
        return generic
    if generic.startswith("sb_publishable_") or generic.startswith("sb_secret_"):
        raise RuntimeError(
            "SUPABASE_KEY looks like a new Supabase publishable/secret prefix (sb_*). "
            "The Python `supabase` client needs the legacy anon JWT: Supabase → Project Settings → API → "
            "**anon public** key (starts with `eyJ`). Set SUPABASE_KEY or SUPABASE_ANON_KEY, "
            "or SUPABASE_SERVICE_KEY with the **service_role** JWT."
        )
    if not generic:
        raise RuntimeError(
            "SUPABASE_KEY is not set. Add the anon JWT (`eyJ...`) to Streamlit Secrets as SUPABASE_KEY "
            "or SUPABASE_ANON_KEY."
        )
    return generic


def format_supabase_connection_error(exc: Exception) -> str:
    msg = str(exc)
    if isinstance(exc, RuntimeError):
        return msg
    if "Name or service not known" in msg or "Errno -2" in msg or "getaddrinfo" in msg.lower():
        try:
            url = get_supabase_project_url()
        except RuntimeError as re:
            return str(re)
        return (
            f"Cannot reach Supabase at {url} (DNS lookup failed). "
            "Fix SUPABASE_URL in Streamlit Secrets — use https://YOUR_REF.supabase.co from "
            "Project Settings → API, with no typos or extra quotes."
        )
    if "Invalid API key" in msg or "JWT" in msg or "PGRST301" in msg:
        return (
            f"{msg} — Use the **anon** JWT (`eyJ...`) or **service_role** JWT in secrets; "
            "not the `sb_publishable_...` dashboard key for Python."
        )
    return f"Supabase error: {msg}"
