import streamlit as st
from datetime import datetime, timedelta
from frontend.utils.api import api_get, api_post, api_delete


def render():
    st.title("📅 Interview Scheduling")

    tab1, tab2 = st.tabs(["Scheduled Interviews", "Schedule New"])

    with tab1:
        interviews = api_get("/interviews/") or []
        if not interviews:
            st.info("No interviews scheduled yet.")
        else:
            for iv in interviews:
                candidate_info = iv.get("candidates", {}) or {}
                cand_name = candidate_info.get("name", iv.get("candidate_id", "Unknown"))
                scheduled = iv.get("scheduled_at", "")
                try:
                    dt = datetime.fromisoformat(scheduled.replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y at %I:%M %p")
                except Exception:
                    date_str = scheduled

                with st.expander(f"📅 {cand_name} — {date_str}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Type:** {iv.get('interview_type', 'video').title()}")
                        if iv.get("meeting_link"):
                            st.markdown(f"**Meeting Link:** [{iv['meeting_link']}]({iv['meeting_link']})")
                        if iv.get("notes"):
                            st.markdown(f"**Notes:** {iv['notes']}")
                    with col2:
                        if st.button("✅ Mark Complete", key=f"comp_{iv['id']}", use_container_width=True):
                            api_post(f"/interviews/{iv['id']}/complete")
                            st.success("Marked as completed")
                            st.rerun()
                        if st.button("🗑️ Cancel", key=f"del_iv_{iv['id']}", use_container_width=True):
                            api_delete(f"/interviews/{iv['id']}")
                            st.rerun()

    with tab2:
        st.subheader("Schedule an Interview")
        jobs = api_get("/jobs/") or []
        job_map = {j["title"]: j["id"] for j in jobs}

        selected_job = st.selectbox("Select Job", list(job_map.keys()))
        if selected_job:
            candidates = api_get("/candidates/", params={"job_id": job_map[selected_job]}) or []
            eligible = [c for c in candidates if c.get("status") not in ("rejected", "selected")]
            cand_map = {f"{c['name']} (Score: {c.get('ai_score', 0)})": c["id"] for c in eligible}

            if not cand_map:
                st.info("No eligible candidates for this job.")
            else:
                selected_cand = st.selectbox("Select Candidate", list(cand_map.keys()))

                col1, col2 = st.columns(2)
                with col1:
                    interview_date = st.date_input("Interview Date", min_value=datetime.today().date())
                    interview_time = st.time_input("Interview Time", value=datetime.now().replace(hour=10, minute=0).time())
                with col2:
                    interview_type = st.selectbox("Interview Type", ["video", "phone", "in-person"])
                    meeting_link = st.text_input("Meeting Link (optional)", placeholder="https://meet.google.com/...")

                notes = st.text_area("Notes (optional)", placeholder="Topics to cover, special instructions...")

                if st.button("Schedule Interview", type="primary", use_container_width=True):
                    scheduled_dt = datetime.combine(interview_date, interview_time)
                    result = api_post("/interviews/", json={
                        "candidate_id": cand_map[selected_cand],
                        "scheduled_at": scheduled_dt.isoformat(),
                        "interview_type": interview_type,
                        "meeting_link": meeting_link or None,
                        "notes": notes or None,
                    })
                    if result:
                        st.success(f"Interview scheduled for {scheduled_dt.strftime('%b %d, %Y at %I:%M %p')}")
                        st.rerun()
