from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import (
    InterviewScheduleRequest,
    ProcessResumeResponse,
    ScheduleInterviewResponse,
)
from app.services import email_service, gemini_service
from app.services.resume_parser import guess_email, parse_resume

app = FastAPI(
    title="Recruitment Agent API",
    description="Analyze resumes, generate interview questions, schedule interviews via email.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for last processed session (demo; use DB in production)
_session_store: dict = {}


@app.get("/health")
def health():
    return {"status": "ok", "service": "recruitment-agent"}


@app.post("/api/resume/analyze", response_model=ProcessResumeResponse)
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    job_role: str = Form(default="Software Engineer"),
    question_count: int = Form(default=10),
):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Empty file")

    try:
        resume_text = parse_resume(content, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    if len(resume_text.strip()) < 50:
        raise HTTPException(400, "Could not extract enough text from resume.")

    try:
        analysis = gemini_service.analyze_resume(resume_text, job_role)
        if not analysis.email:
            guessed = guess_email(resume_text)
            if guessed:
                analysis.email = guessed

        questions = gemini_service.generate_interview_questions(
            resume_text, analysis, job_role, question_count
        )
    except ValueError as e:
        raise HTTPException(503, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"AI processing failed: {e}") from e

    _session_store["last"] = {
        "analysis": analysis,
        "questions": questions,
        "resume_text": resume_text,
        "job_role": job_role,
    }

    preview = resume_text[:500] + ("..." if len(resume_text) > 500 else "")
    return ProcessResumeResponse(
        analysis=analysis,
        questions=questions,
        resume_text_preview=preview,
    )


@app.get("/api/session/latest")
def get_latest_session():
    data = _session_store.get("last")
    if not data:
        raise HTTPException(404, "No resume processed yet.")
    return {
        "analysis": data["analysis"],
        "questions": data["questions"],
        "job_role": data["job_role"],
    }


@app.post("/api/interview/schedule", response_model=ScheduleInterviewResponse)
async def schedule_interview(request: InterviewScheduleRequest):
    data = _session_store.get("last")
    if not data:
        raise HTTPException(
            400,
            "Process a resume first before scheduling an interview.",
        )

    analysis = data["analysis"]
    questions = data["questions"]
    job_role = request.job_role or data.get("job_role", "Open Position")

    candidate_ok = email_service.send_candidate_interview_email(
        candidate_email=request.candidate_email,
        candidate_name=request.candidate_name,
        interview_datetime=request.interview_datetime,
        interview_mode=request.interview_mode,
        job_role=job_role,
        meeting_link=request.meeting_link,
        notes=request.notes,
    )

    hr_ok = email_service.send_hr_interview_pack(
        analysis=analysis,
        questions=questions,
        candidate_name=request.candidate_name,
        candidate_email=request.candidate_email,
        interview_datetime=request.interview_datetime,
        job_role=job_role,
        interview_mode=request.interview_mode,
        meeting_link=request.meeting_link,
    )

    if not candidate_ok and not hr_ok:
        return ScheduleInterviewResponse(
            success=False,
            message=(
                "Emails not sent. Configure SMTP_USER, SMTP_PASSWORD, and HR_EMAIL in .env. "
                "Analysis and questions are still available in the UI."
            ),
            candidate_notified=False,
            hr_notified=False,
        )

    parts = []
    if candidate_ok:
        parts.append("candidate notified")
    if hr_ok:
        parts.append("HR received question pack")
    if not candidate_ok:
        parts.append("candidate email failed (check SMTP)")
    if not hr_ok:
        parts.append("HR email failed (check HR_EMAIL / SMTP)")

    return ScheduleInterviewResponse(
        success=candidate_ok or hr_ok,
        message="; ".join(parts).capitalize() + ".",
        candidate_notified=candidate_ok,
        hr_notified=hr_ok,
    )


@app.post("/api/interview/schedule-with-upload")
async def schedule_with_fresh_analysis(
    file: UploadFile = File(...),
    candidate_email: str = Form(...),
    candidate_name: str = Form(...),
    interview_datetime: str = Form(...),
    job_role: str = Form(default="Software Engineer"),
    interview_mode: str = Form(default="Video Call"),
    meeting_link: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None),
    question_count: int = Form(default=10),
):
    """One-shot: analyze resume + schedule in a single request."""
    analyze_resp = await analyze_resume_endpoint(
        file=file, job_role=job_role, question_count=question_count
    )
    try:
        dt = datetime.fromisoformat(interview_datetime.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.strptime(interview_datetime, "%Y-%m-%dT%H:%M")

    schedule_req = InterviewScheduleRequest(
        candidate_email=candidate_email,
        candidate_name=candidate_name,
        interview_datetime=dt,
        interview_mode=interview_mode,
        meeting_link=meeting_link,
        job_role=job_role,
        notes=notes,
    )
    schedule_resp = await schedule_interview(schedule_req)
    return {
        "analysis": analyze_resp.analysis,
        "questions": analyze_resp.questions,
        "schedule": schedule_resp,
    }
