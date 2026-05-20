import streamlit as st
from frontend.utils.auth import logout


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style='text-align:center; padding: 16px 0 8px;'>
                <span style='font-size:2rem;'>🤖</span>
                <h2 style='margin:4px 0; color:#4F46E5;'>RecruitAI</h2>
                <p style='color:#6B7280; font-size:0.8rem; margin:0;'>Powered by Gemini</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        pages = {
            "📊 Dashboard": "dashboard",
            "💼 Jobs": "jobs",
            "👥 Candidates": "candidates",
            "🤖 AI Analysis": "ai_analysis",
            "📅 Interviews": "interviews",
            "📧 Emails": "emails",
        }

        if "page" not in st.session_state:
            st.session_state["page"] = "dashboard"

        for label, key in pages.items():
            active = st.session_state["page"] == key
            btn_style = "primary" if active else "secondary"
            if st.button(label, use_container_width=True, type=btn_style, key=f"nav_{key}"):
                st.session_state["page"] = key
                st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
