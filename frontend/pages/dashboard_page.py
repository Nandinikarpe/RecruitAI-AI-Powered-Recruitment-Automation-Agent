import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils.api import api_get


def render():
    st.title("📊 HR Dashboard")
    st.caption("Real-time recruitment analytics")

    stats = api_get("/analytics/dashboard")
    if not stats:
        st.warning("Could not load dashboard data.")
        return

    # KPI cards
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "Total Candidates", stats["total_candidates"], "👥"),
        (c2, "Active Jobs", stats["active_jobs"], "💼"),
        (c3, "Interviews", stats["total_interviews"], "📅"),
        (c4, "Avg AI Score", f"{stats['avg_ai_score']}/100", "🤖"),
        (c5, "Total Jobs", stats["total_jobs"], "📋"),
    ]
    for col, label, value, icon in metrics:
        with col:
            st.metric(f"{icon} {label}", value)

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Candidate Status Breakdown")
        status_data = stats.get("status_breakdown", {})
        if status_data:
            colors = {
                "pending": "#F59E0B",
                "scheduled": "#3B82F6",
                "completed": "#8B5CF6",
                "rejected": "#EF4444",
                "selected": "#10B981",
            }
            fig = go.Figure(data=[go.Pie(
                labels=list(status_data.keys()),
                values=list(status_data.values()),
                hole=0.4,
                marker_colors=[colors.get(k, "#6B7280") for k in status_data.keys()],
            )])
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=280, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No candidate data yet.")

    with col_right:
        st.subheader("AI Score Distribution")
        score_data = stats.get("score_distribution", {})
        if score_data:
            fig = px.bar(
                x=list(score_data.keys()),
                y=list(score_data.values()),
                color=list(score_data.values()),
                color_continuous_scale="Viridis",
                labels={"x": "Score Range", "y": "Candidates"},
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No score data yet.")

    st.subheader("Candidates per Job")
    per_job = stats.get("candidates_per_job", [])
    if per_job:
        fig = px.bar(
            per_job,
            x="job",
            y="count",
            color="count",
            color_continuous_scale="Blues",
            labels={"job": "Job Title", "count": "Candidates"},
        )
        fig.update_layout(margin=dict(t=0, b=20, l=0, r=0), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No job data yet.")
