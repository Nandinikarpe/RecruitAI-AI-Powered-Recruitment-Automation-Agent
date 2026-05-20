import json
import re
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config import get_settings
from app.models.schemas import InterviewQuestion, ResumeAnalysis

# Fast + free-tier friendly (lite/8b models respond quicker than full flash)
DEFAULT_MODEL = "gemini-2.0-flash-lite"
FALLBACK_MODELS = (
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
)

RESUME_MAX_CHARS = 5000
GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.2,
    max_output_tokens=2048,
    top_p=0.85,
)


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
    return genai.GenerativeModel(
        model_name,
        generation_config=GENERATION_CONFIG,
    )


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
        return min(float(m.group(1)) + 2, 60)
    if "429" in msg or "quota" in msg.lower():
        return 30
    return 3


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
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": 90},
                )
                return response.text
            except Exception as e:
                last_err = e
                if _is_quota_error(e) and attempt == 0:
                    time.sleep(_retry_seconds(e))
                    continue
                break
    raise ValueError(
        "Gemini API quota exceeded. Wait a minute and retry, or set "
        f"GEMINI_MODEL={DEFAULT_MODEL} in .env / Streamlit Secrets. "
        f"Details: {last_err}"
    ) from last_err


def process_resume(
    resume_text: str,
    job_role: str = "General",
    question_count: int = 8,
) -> tuple[ResumeAnalysis, list[InterviewQuestion]]:
    """Single fast API call: concise analysis + interview questions."""
    excerpt = resume_text[:RESUME_MAX_CHARS]
    prompt = f"""Recruiter for "{job_role}". Be concise. JSON only, no markdown.

Tasks: parse resume, output analysis + exactly {question_count} short interview questions.

JSON schema:
{{"analysis":{{"candidate_name":"","email":null,"phone":null,"skills":[],"experience_years":null,"education":[],"summary":"one sentence","strengths":[],"gaps":[]}},"questions":[{{"category":"Technical|Behavioral|Situational","question":"","rationale":"max 8 words"}}]}}

RESUME:
{excerpt}
"""
    data = _extract_json(_generate(prompt))
    analysis = ResumeAnalysis(**data["analysis"])
    questions = [InterviewQuestion(**q) for q in data.get("questions", [])]
    return analysis, questions[:question_count]


def analyze_resume(resume_text: str, job_role: str = "General") -> ResumeAnalysis:
    analysis, _ = process_resume(resume_text, job_role, question_count=5)
    return analysis


def generate_interview_questions(
    resume_text: str,
    analysis: ResumeAnalysis,
    job_role: str = "General",
    count: int = 8,
) -> list[InterviewQuestion]:
    _, questions = process_resume(resume_text, job_role, question_count=count)
    return questions[:count]
