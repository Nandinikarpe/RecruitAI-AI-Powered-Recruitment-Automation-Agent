import os
from datetime import datetime, timedelta
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

st.set_page_config(
    page_title="Recruitment Agent",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Recruitment Agent")
st.caption(
    "Upload a resume → AI analysis & interview questions (Gemini) → "
    "Schedule interview & email candidate + HR"
)

if "analysis" not in st.session_state:
    st.session_state.analysis = None
    st.session_state.questions = None
    st.session_state.job_role = "Software Engineer"

with st.sidebar:
    st.header("Settings")
    api_url = st.text_input("API URL", value=API_BASE)
    job_role = st.text_input("Job role", value=st.session_state.job_role)
    question_count = st.slider("Number of questions", 5, 20, 10)
    st.divider()
    st.markdown("**API status**")
    try:
        r = requests.get(f"{api_url}/health", timeout=3)
        if r.ok and r.json().get("service") == "recruitment-agent":
            st.success("API online")
        elif r.ok:
            st.warning("Port in use by another app — use port 8001 or stop the other server")
        else:
            st.error("API error")
    except requests.RequestException:
        st.error("API offline")
        st.code("run_api.bat", language="text")
        st.caption("Start the API in a separate terminal, then refresh this page.")

tab_upload, tab_schedule, tab_questions = st.tabs(
    ["1. Resume & Analysis", "2. Schedule Interview", "3. HR Questions"]
)

with tab_upload:
    st.subheader("Upload resume")
    uploaded = st.file_uploader(
        "PDF, DOCX, or TXT",
        type=["pdf", "docx", "txt"],
    )

    if st.button("Analyze resume & generate questions", type="primary", disabled=not uploaded):
        with st.spinner("Gemini is analyzing the resume..."):
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
            data = {"job_role": job_role, "question_count": question_count}
            try:
                resp = requests.post(
                    f"{api_url}/api/resume/analyze",
                    files=files,
                    data=data,
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                st.session_state.analysis = result["analysis"]
                st.session_state.questions = result["questions"]
                st.session_state.job_role = job_role
                st.success("Resume analyzed successfully!")
            except requests.HTTPError as e:
                detail = e.response.text if e.response is not None else str(e)
                st.error(f"API error: {detail}")
            except requests.RequestException as e:
                st.error(f"Could not reach API: {e}")

    if st.session_state.analysis:
        a = st.session_state.analysis
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Candidate profile")
            st.write(f"**Name:** {a.get('candidate_name', 'N/A')}")
            st.write(f"**Email:** {a.get('email') or '—'}")
            st.write(f"**Phone:** {a.get('phone') or '—'}")
            st.write(f"**Experience:** {a.get('experience_years') or 'N/A'} years")
        with col2:
            st.markdown("### Skills")
            skills = a.get("skills", [])[:12]
            if skills:
                st.write(" · ".join(f"`{s}`" for s in skills))
        st.markdown("### Summary")
        st.info(a.get("summary", ""))
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Strengths**")
            for s in a.get("strengths", []):
                st.write(f"- {s}")
        with c2:
            st.markdown("**Areas to probe**")
            for g in a.get("gaps", []):
                st.write(f"- {g}")

with tab_schedule:
    st.subheader("Schedule interview & send emails")
    if not st.session_state.analysis:
        st.warning("Analyze a resume in tab 1 first.")
    else:
        a = st.session_state.analysis
        default_name = a.get("candidate_name") or "Candidate"
        default_email = a.get("email") or ""

        with st.form("schedule_form"):
            c1, c2 = st.columns(2)
            with c1:
                candidate_name = st.text_input("Candidate name", value=default_name)
                candidate_email = st.text_input("Candidate email *", value=default_email)
            with c2:
                interview_date = st.date_input(
                    "Interview date",
                    value=datetime.now().date() + timedelta(days=3),
                )
                interview_time = st.time_input(
                    "Interview time",
                    value=datetime.strptime("10:00", "%H:%M").time(),
                )
            interview_mode = st.selectbox(
                "Mode",
                ["Video Call", "In-person", "Phone"],
            )
            meeting_link = st.text_input("Meeting link (optional)")
            notes = st.text_area("Notes for candidate (optional)")
            submitted = st.form_submit_button("Send schedule to candidate & HR", type="primary")

        if submitted:
            if not candidate_email:
                st.error("Candidate email is required.")
            else:
                dt = datetime.combine(interview_date, interview_time)
                payload = {
                    "candidate_email": candidate_email,
                    "candidate_name": candidate_name,
                    "interview_datetime": dt.isoformat(),
                    "interview_mode": interview_mode,
                    "meeting_link": meeting_link or None,
                    "job_role": st.session_state.job_role,
                    "notes": notes or None,
                }
                with st.spinner("Sending emails..."):
                    try:
                        resp = requests.post(
                            f"{api_url}/api/interview/schedule",
                            json=payload,
                            timeout=30,
                        )
                        resp.raise_for_status()
                        out = resp.json()
                        if out.get("candidate_notified"):
                            st.success(f"Interview invite sent to {candidate_email}")
                        if out.get("hr_notified"):
                            st.success("HR received interview questions by email")
                        if not out.get("success"):
                            st.warning(out.get("message", "Partial failure"))
                    except requests.HTTPError as e:
                        st.error(e.response.text if e.response else str(e))
                    except requests.RequestException as e:
                        st.error(str(e))

with tab_questions:
    st.subheader("Interview questions for HR")
    if not st.session_state.questions:
        st.info("Questions appear after resume analysis.")
    else:
        st.download_button(
            "Download questions (JSON)",
            data=str(st.session_state.questions),
            file_name="interview_questions.json",
            mime="application/json",
        )
        for i, q in enumerate(st.session_state.questions, 1):
            with st.expander(f"Q{i}: [{q.get('category', 'General')}]"):
                st.write(q.get("question", ""))
                if q.get("rationale"):
                    st.caption(f"Why: {q['rationale']}")
