import streamlit as st
from frontend.utils.api import api_get, api_post, api_patch, api_delete


STATUS_COLORS = {
    "pending": "🟡",
    "scheduled": "🔵",
    "completed": "🟣",
    "rejected": "🔴",
    "selected": "🟢",
}


def render():
    st.title("👥 Candidates")

    tab1, tab2 = st.tabs(["Candidate List", "Upload Resume"])

    with tab1:
        jobs = api_get("/jobs/") or []
        job_options = {"All Jobs": None} | {j["title"]: j["id"] for j in jobs}

        col1, col2 = st.columns(2)
        with col1:
            selected_job_label = st.selectbox("Filter by Job", list(job_options.keys()))
        with col2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "pending", "scheduled", "completed", "rejected", "selected"],
            )

        params = {}
        if job_options[selected_job_label]:
            params["job_id"] = job_options[selected_job_label]
        if status_filter != "All":
            params["status"] = status_filter

        candidates = api_get("/candidates/", params=params) or []

        if not candidates:
            st.info("No candidates found.")
        else:
            st.caption(f"Showing {len(candidates)} candidate(s), sorted by AI score")
            for c in candidates:
                score = c.get("ai_score") or 0
                status_icon = STATUS_COLORS.get(c.get("status", "pending"), "⚪")
                score_color = "#10B981" if score >= 70 else "#F59E0B" if score >= 50 else "#EF4444"

                with st.expander(
                    f"{status_icon} {c['name']} — Score: {score}/100 | {c.get('status', 'pending').title()}",
                    expanded=False,
                ):
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**Email:** {c.get('email', 'N/A')}")
                        st.markdown(f"**Phone:** {c.get('phone', 'N/A')}")
                        st.markdown(f"**Experience:** {c.get('experience_years', 'N/A')} years")
                        st.markdown(f"**Education:** {c.get('education', 'N/A')}")

                        skills = c.get("skills", [])
                        if skills:
                            st.markdown("**Skills:** " + " ".join(f"`{s}`" for s in skills))

                        missing = c.get("skills_missing", [])
                        if missing:
                            st.markdown("**Missing Skills:** " + " ".join(f"`{s}`" for s in missing))

                        if c.get("ai_summary"):
                            st.info(f"🤖 {c['ai_summary']}")

                        if c.get("resume_url"):
                            st.markdown(f"[📄 View Resume]({c['resume_url']})")

                    with col_actions:
                        st.markdown(
                            f"<div style='text-align:center; font-size:2rem; color:{score_color};'>"
                            f"<b>{score}</b><br><small>AI Score</small></div>",
                            unsafe_allow_html=True,
                        )
                        new_status = st.selectbox(
                            "Update Status",
                            ["pending", "scheduled", "completed", "rejected", "selected"],
                            index=["pending", "scheduled", "completed", "rejected", "selected"].index(
                                c.get("status", "pending")
                            ),
                            key=f"status_{c['id']}",
                        )
                        if st.button("Update", key=f"upd_{c['id']}", use_container_width=True):
                            api_patch(f"/candidates/{c['id']}/status", params={"status": new_status})
                            st.success("Status updated")
                            st.rerun()

                        if st.button("🗑️ Delete", key=f"del_{c['id']}", use_container_width=True):
                            api_delete(f"/candidates/{c['id']}")
                            st.rerun()

    with tab2:
        st.subheader("Upload Resume")
        jobs = api_get("/jobs/") or []
        active_jobs = [j for j in jobs if j.get("is_active")]

        if not active_jobs:
            st.warning("No active jobs. Please create a job first.")
            return

        job_map = {j["title"]: j["id"] for j in active_jobs}
        selected_job = st.selectbox("Select Job *", list(job_map.keys()))
        uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

        if uploaded_file and st.button("Upload & Analyze", type="primary", use_container_width=True):
            with st.spinner("Parsing resume and running AI analysis..."):
                result = api_post(
                    "/candidates/upload",
                    data={"job_id": job_map[selected_job]},
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                )
            if result:
                st.success(f"✅ Candidate **{result['name']}** added with AI score **{result.get('ai_score', 0)}/100**")
                if result.get("ai_summary"):
                    st.info(f"🤖 {result['ai_summary']}")
