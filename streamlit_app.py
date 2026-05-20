import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app.config import _apply_streamlit_secrets, get_settings
from app.models.schemas import InterviewQuestion, ResumeAnalysis
from app.services import email_service, gemini_service
from app.services.resume_parser import guess_email, parse_resume

load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(
    page_title="Recruitment Agent",
    page_icon="📋",
    layout="wide",
)

_apply_streamlit_secrets()
get_settings.cache_clear()

st.title("📋 Recruitment Agent")
st.caption(
    "Upload a resume → AI analysis & interview questions (Gemini) → "
    "Schedule interview & email candidate + HR"
)

if "analysis" not in st.session_state:
    st.session_state.analysis = None
    st.session_state.questions = None
    st.session_state.resume_text = None
    st.session_state.job_role = "Software Engineer"

settings = get_settings()

with st.sidebar:
    st.header("Settings")
    job_role = st.text_input("Job role", value=st.session_state.job_role)
    question_count = st.slider("Number of questions", 5, 20, 10)
    st.divider()
    st.markdown("**Gemini API**")
    if settings.gemini_api_key:
        st.success("API key loaded")
    else:
        st.error("Set GEMINI_API_KEY in `.env`")
    st.markdown("**Email (SMTP)**")
    if settings.smtp_user and settings.hr_email:
        st.success("SMTP configured")
    else:
        st.caption("Optional: set SMTP_USER, SMTP_PASSWORD, HR_EMAIL in `.env`")

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
            try:
                content = uploaded.getvalue()
                resume_text = parse_resume(content, uploaded.name)
                if len(resume_text.strip()) < 50:
                    st.error("Could not extract enough text from resume.")
                else:
                    analysis, questions = gemini_service.process_resume(
                        resume_text, job_role, question_count
                    )
                    if not analysis.email:
                        guessed = guess_email(resume_text)
                        if guessed:
                            analysis.email = guessed
                    st.session_state.analysis = analysis.model_dump()
                    st.session_state.questions = [q.model_dump() for q in questions]
                    st.session_state.resume_text = resume_text
                    st.session_state.job_role = job_role
                    st.success("Resume analyzed successfully!")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Processing failed: {e}")

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
                analysis = ResumeAnalysis(**st.session_state.analysis)
                questions = [
                    InterviewQuestion(**q) for q in st.session_state.questions
                ]
                role = st.session_state.job_role

                with st.spinner("Sending emails..."):
                    candidate_ok = email_service.send_candidate_interview_email(
                        candidate_email=candidate_email,
                        candidate_name=candidate_name,
                        interview_datetime=dt,
                        interview_mode=interview_mode,
                        job_role=role,
                        meeting_link=meeting_link or None,
                        notes=notes or None,
                    )
                    hr_ok = email_service.send_hr_interview_pack(
                        analysis=analysis,
                        questions=questions,
                        candidate_name=candidate_name,
                        candidate_email=candidate_email,
                        interview_datetime=dt,
                        job_role=role,
                        interview_mode=interview_mode,
                        meeting_link=meeting_link or None,
                    )

                if candidate_ok:
                    st.success(f"Interview invite sent to {candidate_email}")
                if hr_ok:
                    st.success("HR received interview questions by email")
                if not candidate_ok and not hr_ok:
                    st.warning(
                        "Emails not sent. Configure SMTP_USER, SMTP_PASSWORD, and HR_EMAIL in `.env`."
                    )
                elif not candidate_ok:
                    st.warning("Candidate email failed — check SMTP settings.")
                elif not hr_ok:
                    st.warning("HR email failed — check HR_EMAIL in `.env`.")

with tab_questions:
    st.subheader("Interview questions for HR")
    if not st.session_state.questions:
        st.info("Questions appear after resume analysis.")
    else:
        st.download_button(
            "Download questions (JSON)",
            data=json.dumps(st.session_state.questions, indent=2),
            file_name="interview_questions.json",
            mime="application/json",
        )
        for i, q in enumerate(st.session_state.questions, 1):
            with st.expander(f"Q{i}: [{q.get('category', 'General')}]"):
                st.write(q.get("question", ""))
                if q.get("rationale"):
                    st.caption(f"Why: {q['rationale']}")
