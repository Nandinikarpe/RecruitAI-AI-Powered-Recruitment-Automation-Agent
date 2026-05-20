import json
import re
import google.generativeai as genai
from backend.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)
model = genai.GenerativeModel(settings.gemini_model)


def _clean_json(text: str) -> str:
    """Strip markdown code fences if present."""
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    return text


def analyze_resume(resume_text: str, job_description: str, required_skills: list[str]) -> dict:
    """
    Returns structured analysis: skills found, score (0-100), summary, experience_years.
    """
    prompt = f"""
You are an expert HR analyst. Analyze the resume below against the job description and required skills.

JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS: {", ".join(required_skills)}

RESUME:
{resume_text[:4000]}

Return ONLY valid JSON with this exact structure:
{{
  "skills_found": ["skill1", "skill2"],
  "skills_missing": ["skill3"],
  "experience_years": 3.5,
  "education": "B.Tech Computer Science",
  "ai_score": 78,
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1"],
  "summary": "2-3 sentence candidate summary"
}}
"""
    response = model.generate_content(prompt)
    return json.loads(_clean_json(response.text))


def generate_interview_questions(
    resume_text: str,
    job_title: str,
    job_description: str,
    num_questions: int = 5,
) -> list[dict]:
    """
    Returns a list of interview questions with category and difficulty.
    """
    prompt = f"""
You are a senior technical interviewer. Generate {num_questions} targeted interview questions
for the candidate below applying for the role of {job_title}.

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME SUMMARY:
{resume_text[:2000]}

Return ONLY valid JSON array:
[
  {{
    "question": "...",
    "category": "Technical|Behavioral|Situational",
    "difficulty": "Easy|Medium|Hard",
    "expected_answer_hint": "..."
  }}
]
"""
    response = model.generate_content(prompt)
    return json.loads(_clean_json(response.text))


def rank_candidates(candidates: list[dict], job_description: str) -> list[dict]:
    """
    Re-ranks a list of candidates by AI score and returns sorted list with rank.
    """
    sorted_candidates = sorted(candidates, key=lambda c: c.get("ai_score", 0), reverse=True)
    for i, c in enumerate(sorted_candidates):
        c["rank"] = i + 1
    return sorted_candidates


def generate_email_content(email_type: str, candidate_name: str, job_title: str, extra: dict = None) -> dict:
    """
    Generates professional email subject + body for invite/rejection/selection.
    """
    extra_info = json.dumps(extra or {})
    prompt = f"""
Generate a professional HR email of type "{email_type}" for:
- Candidate: {candidate_name}
- Job Title: {job_title}
- Extra context: {extra_info}

Email types:
- invite: Interview invitation with schedule details
- rejection: Polite rejection with encouragement
- selection: Congratulations and next steps

Return ONLY valid JSON:
{{
  "subject": "...",
  "body": "Full email body with proper greeting and sign-off"
}}
"""
    response = model.generate_content(prompt)
    return json.loads(_clean_json(response.text))
