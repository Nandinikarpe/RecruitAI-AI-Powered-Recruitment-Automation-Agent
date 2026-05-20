import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_to_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            if val is not None and val != "":
                label = key.replace("_", " ").strip()
                parts.append(f"{label}: {val}" if label else str(val))
        return ", ".join(parts) if parts else str(value)
    if isinstance(value, list):
        return ", ".join(_coerce_to_str(v) for v in value if v)
    return str(value).strip()


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [_coerce_to_str(value)] if value else []
    result = []
    for item in value:
        text = _coerce_to_str(item)
        if text:
            result.append(text)
    return result


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

    @field_validator("candidate_name", "summary", "email", "phone", mode="before")
    @classmethod
    def coerce_optional_str(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, dict):
            return _coerce_to_str(v)
        return str(v).strip() if isinstance(v, (str, int, float)) else v

    @field_validator("skills", "education", "strengths", "gaps", mode="before")
    @classmethod
    def coerce_lists(cls, v: Any) -> list[str]:
        return _coerce_str_list(v)

    @field_validator("experience_years", mode="before")
    @classmethod
    def coerce_experience(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            match = re.search(r"[\d.]+", v)
            return float(match.group()) if match else None
        return None


class InterviewQuestion(BaseModel):
    category: str
    question: str
    rationale: Optional[str] = None

    @field_validator("category", "question", "rationale", mode="before")
    @classmethod
    def coerce_text_fields(cls, v: Any) -> Any:
        if v is None:
            return v
        if isinstance(v, dict):
            return _coerce_to_str(v)
        return str(v).strip() if v else v
