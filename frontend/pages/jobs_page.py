import streamlit as st
from frontend.utils.api import api_get, api_post, api_delete


def render():
    st.title("💼 Job Postings")

    tab1, tab2 = st.tabs(["All Jobs", "Post New Job"])

    with tab1:
        jobs = api_get("/jobs/") or []
        if not jobs:
            st.info("No jobs posted yet. Create one in the 'Post New Job' tab.")
        for job in jobs:
            status_badge = "🟢 Active" if job.get("is_active") else "🔴 Inactive"
            with st.expander(f"{job['title']} — {status_badge}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Location:** {job.get('location', 'N/A')}")
                    st.markdown(f"**Experience:** {job.get('experience_years', 0)} years")
                    if job.get("salary_range"):
                        st.markdown(f"**Salary:** {job['salary_range']}")
                    st.markdown("**Required Skills:**")
                    skills = job.get("required_skills", [])
                    st.markdown(" ".join(f"`{s}`" for s in skills) if skills else "_None listed_")
                    st.markdown("**Description:**")
                    st.write(job.get("description", ""))
                with col2:
                    if st.button("🗑️ Delete", key=f"del_job_{job['id']}"):
                        api_delete(f"/jobs/{job['id']}")
                        st.success("Job deleted")
                        st.rerun()

    with tab2:
        with st.form("new_job_form"):
            st.subheader("Create Job Posting")
            title = st.text_input("Job Title *", placeholder="Senior Python Developer")
            col1, col2 = st.columns(2)
            with col1:
                location = st.text_input("Location *", placeholder="Remote / New York")
                experience = st.number_input("Min Experience (years)", min_value=0, max_value=30, value=2)
            with col2:
                salary = st.text_input("Salary Range", placeholder="$80k - $120k")
            skills_input = st.text_input(
                "Required Skills (comma-separated) *",
                placeholder="Python, FastAPI, PostgreSQL",
            )
            description = st.text_area("Job Description *", height=200, placeholder="Describe the role...")
            submitted = st.form_submit_button("Post Job", type="primary", use_container_width=True)

            if submitted:
                if not all([title, location, skills_input, description]):
                    st.error("Please fill in all required fields.")
                else:
                    skills = [s.strip() for s in skills_input.split(",") if s.strip()]
                    result = api_post("/jobs/", json={
                        "title": title,
                        "description": description,
                        "required_skills": skills,
                        "experience_years": experience,
                        "location": location,
                        "salary_range": salary or None,
                    })
                    if result:
                        st.success(f"Job '{title}' posted successfully!")
                        st.rerun()
