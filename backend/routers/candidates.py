from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from backend.models.schemas import CandidateOut, InterviewStatus
from backend.auth.jwt_handler import get_current_user
from backend.store import get_store
from backend.services.resume_parser import extract_text, extract_email, extract_phone, extract_name
from backend.services.gemini_service import analyze_resume

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("/upload", response_model=CandidateOut)
async def upload_resume(
    job_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    store = get_store()
    job = store.get("jobs", job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file_bytes = await file.read()
    try:
        resume_text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        resume_url = store.save_resume_file(file.filename, file_bytes)
    except Exception:
        resume_url = None

    name = extract_name(resume_text)
    email = extract_email(resume_text)
    phone = extract_phone(resume_text)

    try:
        analysis = analyze_resume(resume_text, job["description"], job.get("required_skills", []))
    except Exception:
        analysis = {"skills_found": [], "experience_years": 0, "ai_score": 0, "summary": "", "education": ""}

    candidate_data = {
        "job_id": job_id,
        "name": name,
        "email": email or "",
        "phone": phone,
        "skills": analysis.get("skills_found", []),
        "experience_years": analysis.get("experience_years"),
        "education": analysis.get("education"),
        "resume_text": resume_text[:5000],
        "resume_url": resume_url,
        "ai_score": analysis.get("ai_score"),
        "ai_summary": analysis.get("summary"),
        "ai_strengths": analysis.get("strengths", []),
        "ai_weaknesses": analysis.get("weaknesses", []),
        "skills_missing": analysis.get("skills_missing", []),
        "status": InterviewStatus.pending.value,
    }

    return store.insert("candidates", candidate_data)


@router.get("/", response_model=List[CandidateOut])
async def list_candidates(
    job_id: Optional[str] = None,
    status: Optional[InterviewStatus] = None,
    current_user=Depends(get_current_user),
):
    store = get_store()
    rows = store.list("candidates", order_by="ai_score", desc=True)
    if job_id:
        rows = [r for r in rows if r.get("job_id") == job_id]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    return rows


@router.get("/{candidate_id}", response_model=CandidateOut)
async def get_candidate(candidate_id: str, current_user=Depends(get_current_user)):
    row = get_store().get("candidates", candidate_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return row


@router.patch("/{candidate_id}/status")
async def update_status(
    candidate_id: str,
    status: InterviewStatus,
    current_user=Depends(get_current_user),
):
    row = get_store().update("candidates", candidate_id, {"status": status})
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return row


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str, current_user=Depends(get_current_user)):
    if not get_store().delete("candidates", candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    return {"message": "Candidate deleted"}
