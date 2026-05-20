import requests
import streamlit as st

from frontend.utils.backend_url import get_backend_url


def get_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(path: str, params: dict = None):
    try:
        r = requests.get(f"{get_backend_url()}{path}", headers=get_headers(), params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_post(path: str, json: dict = None, data: dict = None, files=None):
    try:
        r = requests.post(
            f"{get_backend_url()}{path}",
            headers=get_headers() if not files else {k: v for k, v in get_headers().items()},
            json=json,
            data=data,
            files=files,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_patch(path: str, json: dict = None, params: dict = None):
    try:
        r = requests.patch(f"{get_backend_url()}{path}", headers=get_headers(), json=json, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None


def api_delete(path: str):
    try:
        r = requests.delete(f"{get_backend_url()}{path}", headers=get_headers(), timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error: {e}")
        return None
