import json
import os
from datetime import datetime, timedelta

import requests
import streamlit as st
from jose import jwt
from passlib.context import CryptContext
from supabase import create_client

from frontend.utils.backend_url import get_backend_url

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _http_error_message(r: requests.Response) -> str:
    """FastAPI returns JSON with `detail`; HTML or empty bodies should not crash the UI."""
    try:
        data = r.json()
    except (json.JSONDecodeError, requests.exceptions.JSONDecodeError, ValueError):
        text = (r.text or "").strip()
        return text[:800] if text else f"Server returned HTTP {r.status_code} with no JSON body."

    detail = data.get("detail")
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, dict):
                loc = ".".join(str(x) for x in item.get("loc", ()))
                msg = item.get("msg", "")
                parts.append(f"{loc}: {msg}".strip(": "))
            else:
                parts.append(str(item))
        return "; ".join(parts) if parts else "Request validation failed."
    if detail is not None:
        return str(detail)
    return f"HTTP {r.status_code}"


def _api_reachable() -> bool:
    """If the FastAPI app responds, use it for auth (same as local dev with uvicorn). Cached per session."""
    if os.environ.get("AUTH_VIA_API", "").strip().lower() in ("0", "false", "no"):
        return False
    if os.environ.get("AUTH_VIA_API", "").strip().lower() in ("1", "true", "yes"):
        return True
    if "_auth_via_api_ok" in st.session_state:
        return bool(st.session_state["_auth_via_api_ok"])
    try:
        r = requests.get(f"{get_backend_url()}/", timeout=2)
        ok = r.status_code == 200
    except Exception:
        ok = False
    st.session_state["_auth_via_api_ok"] = ok
    return ok


def _supabase_for_auth():
    url = (os.environ.get("SUPABASE_URL") or "").strip().rstrip("/")
    key = (os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_KEY. Add them to Streamlit Secrets (Cloud) or .env (local). "
            "Optional: SUPABASE_SERVICE_KEY if anon cannot insert into `users`."
        )
    return create_client(url, key)


def _create_session_token(email: str) -> str:
    secret = (os.environ.get("SECRET_KEY") or "").strip()
    if not secret:
        raise RuntimeError(
            "Missing SECRET_KEY (needed for login sessions). Add it to Streamlit Secrets or .env — "
            "use a long random string, same value as the FastAPI app if you use both."
        )
    algo = os.environ.get("ALGORITHM", "HS256")
    try:
        mins = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    except ValueError:
        mins = 60
    expire = datetime.utcnow() + timedelta(minutes=mins)
    return jwt.encode({"sub": email, "exp": expire}, secret, algorithm=algo)


def _login_via_api(email: str, password: str) -> bool:
    base = get_backend_url()
    try:
        r = requests.post(f"{base}/auth/login", json={"email": email, "password": password}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["logged_in"] = True
            return True
        st.error(_http_error_message(r))
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Login failed: cannot reach API at {base} ({e}).")
        return False
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False


def _register_via_api(email: str, password: str, full_name: str) -> bool:
    base = get_backend_url()
    try:
        r = requests.post(
            f"{base}/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
            timeout=15,
        )
        if r.status_code == 200:
            st.success("Account created! Please log in.")
            return True
        st.error(_http_error_message(r))
        return False
    except requests.exceptions.RequestException as e:
        st.error(f"Registration failed: cannot reach API at {base} ({e}).")
        return False
    except Exception as e:
        st.error(f"Registration failed: {e}")
        return False


def _login_direct_supabase(email: str, password: str) -> bool:
    try:
        db = _supabase_for_auth()
        result = db.table("users").select("*").eq("email", email.strip()).execute()
        if not result.data:
            st.error("Invalid credentials")
            return False
        user = result.data[0]
        if not _pwd.verify(password, user["password_hash"]):
            st.error("Invalid credentials")
            return False
        st.session_state["token"] = _create_session_token(user["email"])
        st.session_state["logged_in"] = True
        return True
    except RuntimeError as e:
        st.error(str(e))
        return False
    except Exception as e:
        st.error(f"Login failed (Supabase): {e}")
        return False


def _register_direct_supabase(email: str, password: str, full_name: str) -> bool:
    if not full_name or not full_name.strip():
        st.error("Full name is required")
        return False
    try:
        db = _supabase_for_auth()
        existing = db.table("users").select("id").eq("email", email.strip()).execute()
        if existing.data:
            st.error("Email already registered")
            return False
        hashed = _pwd.hash(password)
        result = db.table("users").insert(
            {
                "email": email.strip(),
                "password_hash": hashed,
                "full_name": full_name.strip(),
            }
        ).execute()
        if not result.data:
            st.error("Registration failed: database returned no row. Check Supabase `users` table and keys.")
            return False
        st.success("Account created! Please log in.")
        return True
    except RuntimeError as e:
        st.error(str(e))
        return False
    except Exception as e:
        st.error(f"Registration failed (Supabase): {e}")
        return False


def login(email: str, password: str) -> bool:
    if not email or not password:
        st.error("Email and password are required")
        return False
    if _api_reachable():
        return _login_via_api(email, password)
    return _login_direct_supabase(email, password)


def register(email: str, password: str, full_name: str) -> bool:
    if not email or not password:
        st.error("Email and password are required")
        return False
    if _api_reachable():
        return _register_via_api(email, password, full_name)
    return _register_direct_supabase(email, password, full_name)


def logout():
    for key in ["token", "logged_in", "_auth_via_api_ok"]:
        st.session_state.pop(key, None)
    st.rerun()


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)
