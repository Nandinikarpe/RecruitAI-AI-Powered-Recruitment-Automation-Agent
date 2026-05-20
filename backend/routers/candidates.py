from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from backend.models.schemas import CandidateOut, InterviewStatus
from backend.auth.jwt_handler import get_current_user
from backend.services.supabase_client import get_supabase_admin
from backend.services.resume_parser import extract_text, extract_email, extract_phone, extract_name
from backend.services.gemini_service import analyze_resume
import uuid

router = APIRouter(prefix="/candidates", tags=["Candidates"])


@router.post("/upload", response_model=CandidateOut)
async def upload_resume(
    job_id: str = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    db = get_supabase_admin()

    # Validate job exists
    job_result = db.table("jobs").select("*").eq("id", job_id).execute()
    if not job_result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_result.data[0]

    # Parse resume
    file_bytes = await file.read()
    try:
        resume_text = extract_text(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Upload to Supabase Storage
    storage_path = f"resumes/{uuid.uuid4()}_{file.filename}"
    try:
        db.storage.from_("resumes").upload(storage_path, file_bytes)
        resume_url = db.storage.from_("resumes").get_public_url(storage_path)
    except Exception:
        resume_url = None

    # Extract basic info
    name = extract_name(resume_text)
    email = extract_email(resume_text)
    phone = extract_phone(resume_text)

    # AI analysis
    try:
        analysis = analyze_resume(resume_text, job["description"], job.get("required_skills", []))
    except Exception as e:
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
        "status": InterviewStatus.pending,
    }

    result = db.table("candidates").insert(candidate_data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save candidate")
    return result.data[0]


@router.get("/", response_model=List[CandidateOut])
async def list_candidates(
    job_id: Optional[str] = None,
    status: Optional[InterviewStatus] = None,
    current_user=Depends(get_current_user),
):
    db = get_supabase_admin()
    query = db.table("candidates").select("*").order("ai_score", desc=True)
    if job_id:
        query = query.eq("job_id", job_id)
    if status:
        query = query.eq("status", status)
    return query.execute().data or []


@router.get("/{candidate_id}", response_model=CandidateOut)
async def get_candidate(candidate_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("candidates").select("*").eq("id", candidate_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return result.data[0]


@router.patch("/{candidate_id}/status")
async def update_status(
    candidate_id: str,
    status: InterviewStatus,
    current_user=Depends(get_current_user),
):
    db = get_supabase_admin()
    result = db.table("candidates").update({"status": status}).eq("id", candidate_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return result.data[0]


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    db.table("candidates").delete().eq("id", candidate_id).execute()
    return {"message": "Candidate deleted"}
