from fastapi import APIRouter, HTTPException, Depends
from backend.models.schemas import EmailRequest, EmailType
from backend.auth.jwt_handler import get_current_user
from backend.store import get_store
from backend.services.gemini_service import generate_email_content
from backend.services.email_service import send_email, format_html_email

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.post("/send")
async def send_candidate_email(req: EmailRequest, current_user=Depends(get_current_user)):
    store = get_store()
    candidate = store.get("candidates", req.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = store.get("jobs", candidate.get("job_id", ""))
    job_title = job["title"] if job else "the position"
    to_email = candidate.get("email")

    if not to_email:
        raise HTTPException(status_code=400, detail="Candidate has no email address")

    extra = {}
    if req.custom_message:
        extra["custom_note"] = req.custom_message

    if req.email_type == EmailType.invite:
        interviews = store.list(
            "interviews",
            filters={"candidate_id": req.candidate_id},
            order_by="created_at",
            desc=True,
            limit=1,
        )
        if interviews:
            iv = interviews[0]
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

    store.insert(
        "email_logs",
        {
            "candidate_id": req.candidate_id,
            "email_type": req.email_type,
            "to_email": to_email,
            "subject": subject,
            "sent_by": current_user.email,
        },
    )

    return {"message": f"Email sent to {to_email}", "subject": subject}


@router.get("/logs/{candidate_id}")
async def get_email_logs(candidate_id: str, current_user=Depends(get_current_user)):
    return get_store().list("email_logs", filters={"candidate_id": candidate_id}, order_by="created_at", desc=True)
