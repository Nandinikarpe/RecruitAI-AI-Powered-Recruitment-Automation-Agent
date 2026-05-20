from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import AIAnalysisRequest, AIQuestionsRequest
from backend.auth.jwt_handler import get_current_user
from backend.services.supabase_client import get_supabase_admin
from backend.services.gemini_service import (
    analyze_resume,
    generate_interview_questions,
    rank_candidates,
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/analyze")
async def analyze_candidate(req: AIAnalysisRequest, current_user=Depends(get_current_user)):
    db = get_supabase_admin()

    candidate = db.table("candidates").select("*").eq("id", req.candidate_id).execute()
    job = db.table("jobs").select("*").eq("id", req.job_id).execute()

    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not job.data:
        raise HTTPException(status_code=404, detail="Job not found")

    c = candidate.data[0]
    j = job.data[0]

    analysis = analyze_resume(
        c.get("resume_text", ""),
        j["description"],
        j.get("required_skills", []),
    )

    # Persist updated scores
    db.table("candidates").update({
        "ai_score": analysis.get("ai_score"),
        "ai_summary": analysis.get("summary"),
        "skills": analysis.get("skills_found", []),
        "skills_missing": analysis.get("skills_missing", []),
        "ai_strengths": analysis.get("strengths", []),
        "ai_weaknesses": analysis.get("weaknesses", []),
        "experience_years": analysis.get("experience_years"),
        "education": analysis.get("education"),
    }).eq("id", req.candidate_id).execute()

    return {"candidate_id": req.candidate_id, "analysis": analysis}


@router.post("/questions")
async def get_interview_questions(req: AIQuestionsRequest, current_user=Depends(get_current_user)):
    db = get_supabase_admin()

    candidate = db.table("candidates").select("*").eq("id", req.candidate_id).execute()
    job = db.table("jobs").select("*").eq("id", req.job_id).execute()

    if not candidate.data or not job.data:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")

    c = candidate.data[0]
    j = job.data[0]

    questions = generate_interview_questions(
        c.get("resume_text", ""),
        j["title"],
        j["description"],
        req.num_questions,
    )

    # Store questions
    db.table("interview_questions").insert({
        "candidate_id": req.candidate_id,
        "job_id": req.job_id,
        "questions": questions,
    }).execute()

    return {"candidate_id": req.candidate_id, "questions": questions}


@router.get("/rank/{job_id}")
async def rank_job_candidates(job_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()

    job = db.table("jobs").select("*").eq("id", job_id).execute()
    if not job.data:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = db.table("candidates").select("*").eq("job_id", job_id).execute()
    ranked = rank_candidates(candidates.data or [], job.data[0]["description"])

    return {"job_id": job_id, "ranked_candidates": ranked}
