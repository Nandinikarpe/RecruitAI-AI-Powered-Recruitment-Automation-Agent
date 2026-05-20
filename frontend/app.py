import streamlit as st
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils.secrets_bootstrap import apply_streamlit_secrets_to_environ

apply_streamlit_secrets_to_environ()

from frontend.utils.auth import is_logged_in
from frontend.components.sidebar import render_sidebar
from frontend.pages import (
    login_page,
    dashboard_page,
    jobs_page,
    candidates_page,
    ai_page,
    interviews_page,
    emails_page,
)

st.set_page_config(
    page_title="RecruitAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal global CSS
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton > button { border-radius: 8px; }
    .stMetric { background: #F9FAFB; border-radius: 8px; padding: 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not is_logged_in():
    login_page.render()
else:
    render_sidebar()
    page = st.session_state.get("page", "dashboard")
    pages = {
        "dashboard": dashboard_page,
        "jobs": jobs_page,
        "candidates": candidates_page,
        "ai_analysis": ai_page,
        "interviews": interviews_page,
        "emails": emails_page,
    }
    pages.get(page, dashboard_page).render()
