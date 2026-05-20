from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ResumeAnalysis(BaseModel):
    candidate_name: str = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience_years: Optional[float] = None
    education: list[str] = Field(default_factory=list)
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class InterviewQuestion(BaseModel):
    category: str
    question: str
    rationale: Optional[str] = None


class InterviewScheduleRequest(BaseModel):
    candidate_email: EmailStr
    candidate_name: str
    interview_datetime: datetime
    interview_mode: str = "Video Call"
    meeting_link: Optional[str] = None
    job_role: str = "Open Position"
    notes: Optional[str] = None


class ProcessResumeResponse(BaseModel):
    analysis: ResumeAnalysis
    questions: list[InterviewQuestion]
    resume_text_preview: str = ""


class ScheduleInterviewResponse(BaseModel):
    success: bool
    message: str
    candidate_notified: bool
    hr_notified: bool
