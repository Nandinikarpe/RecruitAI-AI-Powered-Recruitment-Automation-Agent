from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import InterviewSchedule, InterviewOut, InterviewStatus
from backend.auth.jwt_handler import get_current_user
from backend.store import get_store

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post("/", response_model=InterviewOut)
async def schedule_interview(data: InterviewSchedule, current_user=Depends(get_current_user)):
    store = get_store()
    if not store.get("candidates", data.candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")

    row = store.insert(
        "interviews",
        {
            **data.model_dump(),
            "scheduled_at": data.scheduled_at.isoformat(),
            "created_by": current_user.email,
            "status": "scheduled",
        },
    )
    store.update("candidates", data.candidate_id, {"status": InterviewStatus.scheduled.value})
    return row


@router.get("/", response_model=List[InterviewOut])
async def list_interviews(current_user=Depends(get_current_user)):
    store = get_store()
    rows = store.list("interviews", order_by="scheduled_at")
    for row in rows:
        c = store.get("candidates", row.get("candidate_id", ""))
        if c:
            row["candidates"] = {"name": c.get("name"), "email": c.get("email"), "job_id": c.get("job_id")}
    return rows


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(interview_id: str, current_user=Depends(get_current_user)):
    row = get_store().get("interviews", interview_id)
    if not row:
        raise HTTPException(status_code=404, detail="Interview not found")
    return row


@router.patch("/{interview_id}/complete")
async def complete_interview(interview_id: str, current_user=Depends(get_current_user)):
    store = get_store()
    interview = store.get("interviews", interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    store.update("interviews", interview_id, {"status": "completed"})
    store.update("candidates", interview["candidate_id"], {"status": InterviewStatus.completed.value})
    return {"message": "Interview marked as completed"}


@router.delete("/{interview_id}")
async def cancel_interview(interview_id: str, current_user=Depends(get_current_user)):
    if not get_store().delete("interviews", interview_id):
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"message": "Interview cancelled"}
