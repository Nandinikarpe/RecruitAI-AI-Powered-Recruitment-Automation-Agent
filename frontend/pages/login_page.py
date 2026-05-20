import streamlit as st
from frontend.utils.auth import login, register


def render():
    st.markdown(
        """
        <div style='text-align:center; padding: 40px 0 20px;'>
            <span style='font-size:3rem;'>🤖</span>
            <h1 style='color:#4F46E5; margin:8px 0;'>RecruitAI</h1>
            <p style='color:#6B7280;'>AI-Powered Recruitment Automation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="hr@company.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
                if submitted:
                    if login(email, password):
                        st.rerun()

        with tab2:
            with st.form("register_form"):
                full_name = st.text_input("Full Name", placeholder="Jane Smith")
                email = st.text_input("Email", placeholder="hr@company.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                if submitted:
                    register(email, password, full_name)
