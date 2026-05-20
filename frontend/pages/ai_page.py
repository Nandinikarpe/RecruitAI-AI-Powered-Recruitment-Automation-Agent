import streamlit as st
from frontend.utils.api import api_get, api_post


def render():
    st.title("🤖 AI Analysis")

    tab1, tab2, tab3 = st.tabs(["Re-Analyze Candidate", "Interview Questions", "Rank Candidates"])

    jobs = api_get("/jobs/") or []
    job_map = {j["title"]: j["id"] for j in jobs}

    with tab1:
        st.subheader("Re-run AI Analysis")
        st.caption("Re-analyze a candidate against a job description to refresh their AI score.")

        selected_job = st.selectbox("Select Job", list(job_map.keys()), key="analyze_job")
        if selected_job:
            job_id = job_map[selected_job]
            candidates = api_get("/candidates/", params={"job_id": job_id}) or []
            cand_map = {c["name"]: c["id"] for c in candidates}

            if not cand_map:
                st.info("No candidates for this job.")
            else:
                selected_cand = st.selectbox("Select Candidate", list(cand_map.keys()), key="analyze_cand")
                if st.button("Run AI Analysis", type="primary"):
                    with st.spinner("Analyzing with Gemini AI..."):
                        result = api_post("/ai/analyze", json={
                            "candidate_id": cand_map[selected_cand],
                            "job_id": job_id,
                        })
                    if result:
                        analysis = result.get("analysis", {})
                        col1, col2, col3 = st.columns(3)
                        col1.metric("AI Score", f"{analysis.get('ai_score', 0)}/100")
                        col2.metric("Experience", f"{analysis.get('experience_years', 0)} yrs")
                        col3.metric("Education", analysis.get("education", "N/A"))

                        if analysis.get("summary"):
                            st.info(f"📝 {analysis['summary']}")

                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**✅ Skills Found:**")
                            for s in analysis.get("skills_found", []):
                                st.markdown(f"- {s}")
                        with c2:
                            st.markdown("**❌ Skills Missing:**")
                            for s in analysis.get("skills_missing", []):
                                st.markdown(f"- {s}")

                        if analysis.get("strengths"):
                            st.markdown("**💪 Strengths:**")
                            for s in analysis["strengths"]:
                                st.markdown(f"- {s}")

                        if analysis.get("weaknesses"):
                            st.markdown("**⚠️ Areas to Improve:**")
                            for w in analysis["weaknesses"]:
                                st.markdown(f"- {w}")

    with tab2:
        st.subheader("Generate Interview Questions")
        selected_job = st.selectbox("Select Job", list(job_map.keys()), key="q_job")
        if selected_job:
            job_id = job_map[selected_job]
            candidates = api_get("/candidates/", params={"job_id": job_id}) or []
            cand_map = {c["name"]: c["id"] for c in candidates}

            if not cand_map:
                st.info("No candidates for this job.")
            else:
                selected_cand = st.selectbox("Select Candidate", list(cand_map.keys()), key="q_cand")
                num_q = st.slider("Number of Questions", 3, 10, 5)

                if st.button("Generate Questions", type="primary"):
                    with st.spinner("Generating tailored questions with Gemini AI..."):
                        result = api_post("/ai/questions", json={
                            "candidate_id": cand_map[selected_cand],
                            "job_id": job_id,
                            "num_questions": num_q,
                        })
                    if result:
                        questions = result.get("questions", [])
                        st.success(f"Generated {len(questions)} questions")
                        for i, q in enumerate(questions, 1):
                            diff_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(q.get("difficulty"), "⚪")
                            with st.expander(f"Q{i}: {q['question'][:80]}...", expanded=i == 1):
                                st.markdown(f"**Question:** {q['question']}")
                                st.markdown(f"**Category:** `{q.get('category', 'N/A')}` | **Difficulty:** {diff_color} {q.get('difficulty', 'N/A')}")
                                if q.get("expected_answer_hint"):
                                    st.markdown(f"**Expected Answer Hint:** _{q['expected_answer_hint']}_")

    with tab3:
        st.subheader("Rank Candidates by AI Score")
        selected_job = st.selectbox("Select Job", list(job_map.keys()), key="rank_job")
        if selected_job and st.button("Rank Candidates", type="primary"):
            with st.spinner("Ranking candidates..."):
                result = api_get(f"/ai/rank/{job_map[selected_job]}")
            if result:
                ranked = result.get("ranked_candidates", [])
                if not ranked:
                    st.info("No candidates to rank.")
                else:
                    st.success(f"Ranked {len(ranked)} candidates")
                    for c in ranked:
                        score = c.get("ai_score") or 0
                        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(c.get("rank"), f"#{c.get('rank')}")
                        col1, col2, col3 = st.columns([1, 4, 1])
                        col1.markdown(f"### {medal}")
                        col2.markdown(f"**{c['name']}** — {c.get('email', '')}")
                        col2.markdown(" ".join(f"`{s}`" for s in c.get("skills", [])[:5]))
                        col3.metric("Score", f"{score}/100")
                        st.divider()
