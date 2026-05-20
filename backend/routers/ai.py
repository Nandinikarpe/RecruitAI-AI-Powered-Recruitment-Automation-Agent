from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import AIAnalysisRequest, AIQuestionsRequest
from backend.auth.jwt_handler import get_current_user
from backend.store import get_store
from backend.services.gemini_service import (
    analyze_resume,
    generate_interview_questions,
    rank_candidates,
)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/analyze")
async def analyze_candidate(req: AIAnalysisRequest, current_user=Depends(get_current_user)):
    store = get_store()
    c = store.get("candidates", req.candidate_id)
    j = store.get("jobs", req.job_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")

    analysis = analyze_resume(c.get("resume_text", ""), j["description"], j.get("required_skills", []))

    store.update(
        "candidates",
        req.candidate_id,
        {
            "ai_score": analysis.get("ai_score"),
            "ai_summary": analysis.get("summary"),
            "skills": analysis.get("skills_found", []),
            "skills_missing": analysis.get("skills_missing", []),
            "ai_strengths": analysis.get("strengths", []),
            "ai_weaknesses": analysis.get("weaknesses", []),
            "experience_years": analysis.get("experience_years"),
            "education": analysis.get("education"),
        },
    )

    return {"candidate_id": req.candidate_id, "analysis": analysis}


@router.post("/questions")
async def get_interview_questions(req: AIQuestionsRequest, current_user=Depends(get_current_user)):
    store = get_store()
    c = store.get("candidates", req.candidate_id)
    j = store.get("jobs", req.job_id)
    if not c or not j:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")

    questions = generate_interview_questions(
        c.get("resume_text", ""),
        j["title"],
        j["description"],
        req.num_questions,
    )

    store.insert(
        "interview_questions",
        {"candidate_id": req.candidate_id, "job_id": req.job_id, "questions": questions},
    )

    return {"candidate_id": req.candidate_id, "questions": questions}


@router.get("/rank/{job_id}")
async def rank_job_candidates(job_id: str, current_user=Depends(get_current_user)):
    store = get_store()
    job = store.get("jobs", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    candidates = store.list("candidates", filters={"job_id": job_id})
    ranked = rank_candidates(candidates, job["description"])
    return {"job_id": job_id, "ranked_candidates": ranked}
