from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import EmailRequest, EmailType
from backend.auth.jwt_handler import get_current_user
from backend.services.supabase_client import get_supabase_admin
from backend.services.gemini_service import generate_email_content
from backend.services.email_service import send_email, format_html_email

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.post("/send")
async def send_candidate_email(req: EmailRequest, current_user=Depends(get_current_user)):
    db = get_supabase_admin()

    # Fetch candidate + job
    candidate_res = db.table("candidates").select("*, jobs(title)").eq("id", req.candidate_id).execute()
    if not candidate_res.data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate = candidate_res.data[0]
    job_title = candidate.get("jobs", {}).get("title", "the position") if candidate.get("jobs") else "the position"
    to_email = candidate["email"]

    if not to_email:
        raise HTTPException(status_code=400, detail="Candidate has no email address")

    # Generate AI email content
    extra = {}
    if req.custom_message:
        extra["custom_note"] = req.custom_message

    # Fetch interview details for invite emails
    if req.email_type == EmailType.invite:
        interview = db.table("interviews").select("*").eq("candidate_id", req.candidate_id).order(
            "created_at", desc=True
        ).limit(1).execute()
        if interview.data:
            iv = interview.data[0]
            extra["scheduled_at"] = str(iv.get("scheduled_at"))
            extra["interview_type"] = iv.get("interview_type", "video")
            extra["meeting_link"] = iv.get("meeting_link", "")

    email_content = generate_email_content(req.email_type, candidate["name"], job_title, extra)
    subject = email_content["subject"]
    body = email_content["body"]

    html_body = format_html_email(subject, body, candidate["name"])
    success = send_email(to_email, subject, html_body, html=True)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")

    # Log email
    db.table("email_logs").insert({
        "candidate_id": req.candidate_id,
        "email_type": req.email_type,
        "to_email": to_email,
        "subject": subject,
        "sent_by": current_user.email,
    }).execute()

    return {"message": f"Email sent to {to_email}", "subject": subject}


@router.get("/logs/{candidate_id}")
async def get_email_logs(candidate_id: str, current_user=Depends(get_current_user)):
    db = get_supabase_admin()
    result = db.table("email_logs").select("*").eq("candidate_id", candidate_id).order(
        "created_at", desc=True
    ).execute()
    return result.data or []
