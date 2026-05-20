from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import InterviewSchedule, InterviewOut, InterviewStatus
from backend.auth.jwt_handler import get_current_user
from backend.services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post("/", response_model=InterviewOut)
async def schedule_interview(data: InterviewSchedule, current_user=Depends(get_current_user)):
    db = get_supabase_admin()

    candidate = db.table("candidates").select("*").eq("id", data.candidate_id).execute()
    if not candidate.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    result = db.table("interviews").insert({
        **data.model_dump(),
        "scheduled_at": data.scheduled_at.isoformat(),
        "created_by": current_user.email,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to schedule interview")

    # Update candidate status
    db.table("candidates").update({"status": InterviewStatus.scheduled}).eq("id", data.candidate_id).execute()

    return result.data[0]


@router.get("/", response_model=List[InterviewOut])
async def list_interviews(current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("interviews").select("*, candidates(name, email, job_id)").order("scheduled_at").execute()
    return result.data or []


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(interview_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("interviews").select("*").eq("id", interview_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Interview not found")
    return result.data[0]


@router.patch("/{interview_id}/complete")
async def complete_interview(interview_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    interview = db.table("interviews").select("*").eq("id", interview_id).execute()
    if not interview.data:
        raise HTTPException(status_code=404, detail="Interview not found")

    db.table("interviews").update({"status": "completed"}).eq("id", interview_id).execute()
    db.table("candidates").update({"status": InterviewStatus.completed}).eq(
        "id", interview.data[0]["candidate_id"]
    ).execute()

    return {"message": "Interview marked as completed"}


@router.delete("/{interview_id}")
async def cancel_interview(interview_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    db.table("interviews").delete().eq("id", interview_id).execute()
    return {"message": "Interview cancelled"}
