from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models.schemas import JobCreate, JobOut
from backend.auth.jwt_handler import get_current_user
from backend.services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=JobOut)
async def create_job(job: JobCreate, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("jobs").insert({
        **job.model_dump(),
        "created_by": current_user.email,
        "is_active": True,
    }).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create job")
    return result.data[0]


@router.get("/", response_model=List[JobOut])
async def list_jobs(current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("jobs").select("*").order("created_at", desc=True).execute()
    return result.data or []


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("jobs").select("*").eq("id", job_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return result.data[0]


@router.put("/{job_id}", response_model=JobOut)
async def update_job(job_id: str, job: JobCreate, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("jobs").update(job.model_dump()).eq("id", job_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return result.data[0]


@router.delete("/{job_id}")
async def delete_job(job_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    db.table("jobs").update({"is_active": False}).eq("id", job_id).execute()
    return {"message": "Job deactivated"}
