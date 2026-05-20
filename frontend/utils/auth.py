import json

import requests
import streamlit as st

from frontend.utils.backend_url import get_backend_url


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


def login(email: str, password: str) -> bool:
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
        st.error(
            f"Login failed: cannot reach API at {base} ({e}). "
            "Deploy the FastAPI app and set BACKEND_URL (env or Streamlit secrets) to its public URL."
        )
        return False
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False


def register(email: str, password: str, full_name: str) -> bool:
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
        st.error(
            f"Registration failed: cannot reach API at {base} ({e}). "
            "Deploy the FastAPI app and set BACKEND_URL (env or Streamlit secrets) to its public URL."
        )
        return False
    except Exception as e:
        st.error(f"Registration failed: {e}")
        return False


def logout():
    for key in ["token", "logged_in"]:
        st.session_state.pop(key, None)
    st.rerun()


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)
