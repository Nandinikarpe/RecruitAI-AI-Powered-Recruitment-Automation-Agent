from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InterviewStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    completed = "completed"
    rejected = "rejected"
    selected = "selected"


class EmailType(str, Enum):
    invite = "invite"
    rejection = "rejection"
    selection = "selection"


# Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime


# Job
class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    experience_years: int
    location: str
    salary_range: Optional[str] = None


class JobOut(JobCreate):
    id: str
    created_by: str
    created_at: datetime
    is_active: bool = True


# Candidate
class CandidateOut(BaseModel):
    id: str
    job_id: str
    name: str
    email: str
    phone: Optional[str]
    skills: List[str]
    experience_years: Optional[float]
    education: Optional[str]
    resume_url: Optional[str]
    ai_score: Optional[float]
    ai_summary: Optional[str]
    status: InterviewStatus
    created_at: datetime


# Interview
class InterviewSchedule(BaseModel):
    candidate_id: str
    scheduled_at: datetime
    interview_type: str = "video"
    meeting_link: Optional[str] = None
    notes: Optional[str] = None


class InterviewOut(InterviewSchedule):
    id: str
    created_at: datetime


# Email
class EmailRequest(BaseModel):
    candidate_id: str
    email_type: EmailType
    custom_message: Optional[str] = None


# AI
class AIAnalysisRequest(BaseModel):
    candidate_id: str
    job_id: str


class AIQuestionsRequest(BaseModel):
    candidate_id: str
    job_id: str
    num_questions: int = 5
