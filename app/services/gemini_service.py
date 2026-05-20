import json
import re
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config import get_settings
from app.models.schemas import InterviewQuestion, ResumeAnalysis

# Free-tier friendly models (gemini-2.0-flash often has 0 quota on free tier)
DEFAULT_MODEL = "gemini-1.5-flash"
FALLBACK_MODELS = ("gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash")


def _models_to_try() -> list[str]:
    settings = get_settings()
    primary = settings.gemini_model or DEFAULT_MODEL
    seen = set()
    ordered = []
    for name in (primary, *FALLBACK_MODELS):
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _configure_gemini(model_name: str) -> genai.GenerativeModel:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to .env or Streamlit Secrets "
            "(https://aistudio.google.com/apikey)."
        )
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(model_name)


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def _retry_seconds(err: Exception) -> float:
    msg = str(err)
    m = re.search(r"retry in (\d+(?:\.\d+)?)s", msg, re.I)
    if m:
        return min(float(m.group(1)) + 2, 90)
    if "429" in msg or "quota" in msg.lower():
        return 45
    return 5


def _is_quota_error(err: Exception) -> bool:
    if isinstance(err, google_exceptions.ResourceExhausted):
        return True
    msg = str(err).lower()
    return "429" in msg or "quota" in msg or "rate" in msg


def _generate(prompt: str) -> str:
    last_err: Exception | None = None
    for model_name in _models_to_try():
        model = _configure_gemini(model_name)
        for attempt in range(2):
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_err = e
                if _is_quota_error(e) and attempt == 0:
                    time.sleep(_retry_seconds(e))
                    continue
                break
    raise ValueError(
        "Gemini API quota exceeded. Wait a few minutes and try again, or use "
        f"GEMINI_MODEL={DEFAULT_MODEL} in .env / Streamlit Secrets. "
        f"Details: {last_err}"
    ) from last_err


def process_resume(
    resume_text: str,
    job_role: str = "General",
    question_count: int = 10,
) -> tuple[ResumeAnalysis, list[InterviewQuestion]]:
    """Single API call: analysis + interview questions (saves free-tier quota)."""
    prompt = f"""You are an expert recruiter and interviewer for role: {job_role}.

Analyze the resume and generate {question_count} tailored interview questions in ONE response.

Return ONLY valid JSON:
{{
  "analysis": {{
    "candidate_name": "string",
    "email": "string or null",
    "phone": "string or null",
    "skills": ["skill1"],
    "experience_years": number or null,
    "education": ["degree"],
    "summary": "2-3 sentences",
    "strengths": ["strength1"],
    "gaps": ["gap1"]
  }},
  "questions": [
    {{
      "category": "Technical|Behavioral|Situational|Role-specific",
      "question": "question text",
      "rationale": "why ask this"
    }}
  ]
}}

RESUME:
{resume_text[:10000]}
"""
    data = _extract_json(_generate(prompt))
    analysis = ResumeAnalysis(**data["analysis"])
    questions = [InterviewQuestion(**q) for q in data.get("questions", [])]
    return analysis, questions


def analyze_resume(resume_text: str, job_role: str = "General") -> ResumeAnalysis:
    analysis, _ = process_resume(resume_text, job_role, question_count=5)
    return analysis


def generate_interview_questions(
    resume_text: str,
    analysis: ResumeAnalysis,
    job_role: str = "General",
    count: int = 10,
) -> list[InterviewQuestion]:
    _, questions = process_resume(resume_text, job_role, question_count=count)
    return questions[:count]
