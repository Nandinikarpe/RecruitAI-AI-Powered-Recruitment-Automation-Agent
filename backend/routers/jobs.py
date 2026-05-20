from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import JobCreate, JobOut
from backend.auth.jwt_handler import get_current_user
from backend.store import get_store

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=JobOut)
async def create_job(job: JobCreate, current_user=Depends(get_current_user)):
    store = get_store()
    row = store.insert("jobs", {**job.model_dump(), "created_by": current_user.email, "is_active": True})
    return row


@router.get("/", response_model=List[JobOut])
async def list_jobs(current_user=Depends(get_current_user)):
    return get_store().list("jobs", order_by="created_at", desc=True)


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, current_user=Depends(get_current_user)):
    row = get_store().get("jobs", job_id)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return row


@router.put("/{job_id}", response_model=JobOut)
async def update_job(job_id: str, job: JobCreate, current_user=Depends(get_current_user)):
    row = get_store().update("jobs", job_id, job.model_dump())
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return row


@router.delete("/{job_id}")
async def delete_job(job_id: str, current_user=Depends(get_current_user)):
    row = get_store().update("jobs", job_id, {"is_active": False})
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deactivated"}
