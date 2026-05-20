"""Read Supabase URL/key from env (after Streamlit bootstrap). Prefer JWT anon key over sb_publishable for supabase-py."""

import os
from typing import Optional


def _clean(value: Optional[str]) -> str:
    if not value:
        return ""
    s = str(value).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1].strip()
    return s


def get_supabase_project_url() -> str:
    for k in ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"):
        v = _clean(os.environ.get(k))
        if v:
            return v.rstrip("/")
    return ""


def get_supabase_auth_key() -> str:
    """
    Key for create_client(). Order:
    1. Service role (bypasses RLS)
    2. Legacy anon JWT (eyJ...) — required for many supabase-py versions
    3. SUPABASE_KEY only if it looks like a JWT

    New `sb_publishable_` keys often return "Invalid API key" with supabase-py; we error early with instructions.
    """
    for k in ("SUPABASE_SERVICE_KEY", "SUPABASE_SECRET_KEY"):
        v = _clean(os.environ.get(k))
        if v:
            return v

    anon = _clean(os.environ.get("SUPABASE_ANON_KEY")) or _clean(os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY"))
    generic = _clean(os.environ.get("SUPABASE_KEY")) or _clean(os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"))

    if anon:
        return anon
    if generic.startswith("eyJ"):
        return generic
    if generic.startswith("sb_publishable_") or generic.startswith("sb_secret_"):
        raise RuntimeError(
            "SUPABASE_KEY looks like a new Supabase publishable/secret prefix (sb_*). "
            "The Python `supabase` client needs the legacy anon JWT: open Supabase → Project Settings → API → "
            "**anon** / **public** key (long text starting with `eyJ`). "
            "Put that in Secrets as `SUPABASE_KEY` or `SUPABASE_ANON_KEY`, or use `SUPABASE_SERVICE_KEY` "
            "with the **service_role** JWT from the same page."
        )
    return generic
