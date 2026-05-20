from typing import Optional

from pydantic import BaseModel, Field


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
