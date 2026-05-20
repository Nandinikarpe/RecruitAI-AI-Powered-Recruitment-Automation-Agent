import streamlit as st
from frontend.utils.api import api_get, api_post


EMAIL_DESCRIPTIONS = {
    "invite": "📨 Interview Invitation — Send interview schedule and meeting details",
    "rejection": "❌ Rejection Email — Polite rejection with encouragement",
    "selection": "🎉 Selection Email — Congratulations and next steps",
}


def render():
    st.title("📧 Email Automation")

    tab1, tab2 = st.tabs(["Send Email", "Email Logs"])

    with tab1:
        st.subheader("Send AI-Generated Email")
        st.caption("Gemini AI generates professional, personalized emails automatically.")

        jobs = api_get("/jobs/") or []
        job_map = {j["title"]: j["id"] for j in jobs}

        selected_job = st.selectbox("Select Job", list(job_map.keys()))
        if selected_job:
            candidates = api_get("/candidates/", params={"job_id": job_map[selected_job]}) or []
            cand_map = {f"{c['name']} ({c.get('email', 'no email')})": c for c in candidates}

            if not cand_map:
                st.info("No candidates for this job.")
            else:
                selected_cand_label = st.selectbox("Select Candidate", list(cand_map.keys()))
                candidate = cand_map[selected_cand_label]

                email_type = st.selectbox(
                    "Email Type",
                    ["invite", "rejection", "selection"],
                    format_func=lambda x: EMAIL_DESCRIPTIONS[x],
                )

                custom_message = st.text_area(
                    "Additional Notes (optional)",
                    placeholder="Any specific details to include in the email...",
                )

                # Show candidate info
                with st.expander("Candidate Details", expanded=False):
                    st.markdown(f"**Name:** {candidate['name']}")
                    st.markdown(f"**Email:** {candidate.get('email', 'N/A')}")
                    st.markdown(f"**AI Score:** {candidate.get('ai_score', 0)}/100")
                    st.markdown(f"**Status:** {candidate.get('status', 'pending').title()}")

                if not candidate.get("email"):
                    st.error("This candidate has no email address on file.")
                elif st.button("Send Email", type="primary", use_container_width=True):
                    with st.spinner("Generating and sending email..."):
                        result = api_post("/emails/send", json={
                            "candidate_id": candidate["id"],
                            "email_type": email_type,
                            "custom_message": custom_message or None,
                        })
                    if result:
                        st.success(f"✅ {result['message']}")
                        st.info(f"Subject: {result.get('subject', '')}")

    with tab2:
        st.subheader("Email History")
        jobs = api_get("/jobs/") or []
        job_map = {j["title"]: j["id"] for j in jobs}

        selected_job = st.selectbox("Select Job", list(job_map.keys()), key="log_job")
        if selected_job:
            candidates = api_get("/candidates/", params={"job_id": job_map[selected_job]}) or []
            cand_map = {c["name"]: c["id"] for c in candidates}

            if not cand_map:
                st.info("No candidates.")
            else:
                selected_cand = st.selectbox("Select Candidate", list(cand_map.keys()), key="log_cand")
                logs = api_get(f"/emails/logs/{cand_map[selected_cand]}") or []

                if not logs:
                    st.info("No emails sent to this candidate yet.")
                else:
                    for log in logs:
                        icon = {"invite": "📨", "rejection": "❌", "selection": "🎉"}.get(log.get("email_type"), "📧")
                        st.markdown(
                            f"{icon} **{log.get('email_type', '').title()}** → `{log.get('to_email')}` "
                            f"| _{log.get('subject', '')}_"
                        )
                        st.caption(f"Sent by {log.get('sent_by')} on {log.get('created_at', '')[:10]}")
                        st.divider()
