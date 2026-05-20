from fastapi import APIRouter, Depends
from backend.auth.jwt_handler import get_current_user
from backend.services.supabase_client import get_supabase_admin
from collections import Counter

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def dashboard_stats(current_user=Depends(get_current_user)):
    db = get_supabase_admin()

    candidates = db.table("candidates").select("status, ai_score, job_id, created_at").execute().data or []
    jobs = db.table("jobs").select("id, title, is_active").execute().data or []
    interviews = db.table("interviews").select("scheduled_at, status").execute().data or []

    total_candidates = len(candidates)
    avg_score = round(sum(c["ai_score"] or 0 for c in candidates) / max(total_candidates, 1), 1)
    status_counts = Counter(c["status"] for c in candidates)
    score_distribution = {
        "90-100": sum(1 for c in candidates if (c["ai_score"] or 0) >= 90),
        "70-89": sum(1 for c in candidates if 70 <= (c["ai_score"] or 0) < 90),
        "50-69": sum(1 for c in candidates if 50 <= (c["ai_score"] or 0) < 70),
        "0-49": sum(1 for c in candidates if (c["ai_score"] or 0) < 50),
    }

    # Candidates per job
    job_map = {j["id"]: j["title"] for j in jobs}
    per_job = Counter(c["job_id"] for c in candidates)
    candidates_per_job = [
        {"job": job_map.get(jid, jid), "count": cnt}
        for jid, cnt in per_job.most_common(10)
    ]

    return {
        "total_candidates": total_candidates,
        "total_jobs": len(jobs),
        "active_jobs": sum(1 for j in jobs if j.get("is_active")),
        "total_interviews": len(interviews),
        "avg_ai_score": avg_score,
        "status_breakdown": dict(status_counts),
        "score_distribution": score_distribution,
        "candidates_per_job": candidates_per_job,
    }
