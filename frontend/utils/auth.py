import streamlit as st
import requests

BASE_URL = "http://localhost:8000"


def login(email: str, password: str) -> bool:
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            st.session_state["token"] = data["access_token"]
            st.session_state["logged_in"] = True
            return True
        st.error("Invalid credentials")
        return False
    except Exception as e:
        st.error(f"Login failed: {e}")
        return False


def register(email: str, password: str, full_name: str) -> bool:
    try:
        r = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
            timeout=15,
        )
        if r.status_code == 200:
            st.success("Account created! Please log in.")
            return True
        st.error(r.json().get("detail", "Registration failed"))
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
