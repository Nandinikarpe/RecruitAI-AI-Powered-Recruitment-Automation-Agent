import json
import re

import google.generativeai as genai

from app.config import get_settings
from app.models.schemas import InterviewQuestion, ResumeAnalysis


def _configure_gemini() -> genai.GenerativeModel:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to your .env file "
            "(get a free key at https://aistudio.google.com/apikey)."
        )
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)


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


def analyze_resume(resume_text: str, job_role: str = "General") -> ResumeAnalysis:
    model = _configure_gemini()
    prompt = f"""You are an expert technical recruiter. Analyze this resume for the role: {job_role}.

Return ONLY valid JSON with this exact structure:
{{
  "candidate_name": "string",
  "email": "string or null",
  "phone": "string or null",
  "skills": ["skill1", "skill2"],
  "experience_years": number or null,
  "education": ["degree or school"],
  "summary": "2-3 sentence professional summary",
  "strengths": ["strength1", "strength2"],
  "gaps": ["potential gap or area to probe"]
}}

RESUME:
{resume_text[:12000]}
"""
    response = model.generate_content(prompt)
    data = _extract_json(response.text)
    return ResumeAnalysis(**data)


def generate_interview_questions(
    resume_text: str,
    analysis: ResumeAnalysis,
    job_role: str = "General",
    count: int = 10,
) -> list[InterviewQuestion]:
    model = _configure_gemini()
    analysis_json = analysis.model_dump_json()
    prompt = f"""You are a senior interviewer. Generate {count} tailored interview questions
based on this resume and analysis for role: {job_role}.

Mix categories: technical, behavioral, situational, role-specific.
Questions must reference specific resume details when possible.

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "category": "Technical|Behavioral|Situational|Role-specific",
      "question": "the question",
      "rationale": "why this question matters"
    }}
  ]
}}

ANALYSIS:
{analysis_json}

RESUME (excerpt):
{resume_text[:8000]}
"""
    response = model.generate_content(prompt)
    data = _extract_json(response.text)
    return [InterviewQuestion(**q) for q in data.get("questions", [])]
