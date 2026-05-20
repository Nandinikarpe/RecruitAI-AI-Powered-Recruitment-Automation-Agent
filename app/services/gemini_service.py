import json
import re
import time

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.config import get_settings
from app.models.schemas import InterviewQuestion, ResumeAnalysis

# Prefer fast models that work on free tier (2.0-flash-lite often quota=0)
MODEL_PRIORITY = (
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.5-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
)

RESUME_MAX_CHARS = 5000
GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.2,
    max_output_tokens=2048,
    top_p=0.85,
)

CHAT_GENERATION_CONFIG = genai.GenerationConfig(
    temperature=0.7,
    max_output_tokens=1024,
    top_p=0.9,
)

CHAT_RESUME_EXCERPT = 2500

_active_model: str | None = None
_available_models: set[str] | None = None
_quota_blocked: set[str] = set()


def _normalize_model_name(name: str) -> str:
    return name.removeprefix("models/")


def list_generative_models() -> list[str]:
    """Return model IDs that support generateContent for this API key."""
    global _available_models
    if _available_models is not None:
        return sorted(_available_models)

    settings = get_settings()
    if not settings.gemini_api_key:
        return []

    genai.configure(api_key=settings.gemini_api_key)
    names: set[str] = set()
    for m in genai.list_models():
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            names.add(_normalize_model_name(m.name))

    _available_models = names
    return sorted(names)


def get_active_model() -> str:
    """Model used for the last successful (or next) request."""
    if _active_model:
        return _active_model
    models = _models_to_try()
    return models[0] if models else "gemini-2.5-flash-lite"


def _models_to_try() -> list[str]:
    global _active_model
    settings = get_settings()
    configured = (settings.gemini_model or "").strip().lower()

    ordered: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        name = _normalize_model_name(name)
        if name and name not in seen and name not in _quota_blocked:
            seen.add(name)
            ordered.append(name)

    # Explicit model from .env (skip "auto")
    if configured and configured not in ("auto", "automatic"):
        add(settings.gemini_model)

    if _active_model:
        add(_active_model)

    available = set(list_generative_models())
    for name in MODEL_PRIORITY:
        if not available or name in available:
            add(name)

    if not ordered:
        add("gemini-2.5-flash-lite")

    return ordered


def _configure_gemini(
    model_name: str,
    *,
    generation_config: genai.GenerationConfig | None = None,
    system_instruction: str | None = None,
) -> genai.GenerativeModel:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Add it to .env or Streamlit Secrets "
            "(https://aistudio.google.com/apikey)."
        )
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name,
        generation_config=generation_config or GENERATION_CONFIG,
        system_instruction=system_instruction,
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


def _mark_model_failed(model_name: str, err: Exception) -> None:
    global _active_model
    if _is_quota_error(err):
        _quota_blocked.add(model_name)
    if _active_model == model_name:
        _active_model = None


def _mark_model_success(model_name: str) -> None:
    global _active_model
    _active_model = model_name


def _generate(prompt: str, *, generation_config: genai.GenerationConfig | None = None) -> str:
    last_err: Exception | None = None
    for model_name in _models_to_try():
        model = _configure_gemini(model_name, generation_config=generation_config)
        for attempt in range(2):
            try:
                response = model.generate_content(
                    prompt,
                    request_options={"timeout": 90},
                )
                _mark_model_success(model_name)
                return response.text
            except Exception as e:
                last_err = e
                _mark_model_failed(model_name, e)
                if _is_quota_error(e) and attempt == 0:
                    time.sleep(_retry_seconds(e))
                    continue
                break

    tried = ", ".join(_models_to_try()[:5])
    raise ValueError(
        f"No working Gemini model (tried: {tried}). "
        "Set GEMINI_MODEL=auto in .env or wait for quota reset. "
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


def _build_chat_system_prompt(
    job_role: str,
    analysis: dict | None,
    questions: list | None,
    resume_text: str | None,
) -> str:
    lines = [
        "You are RecruitAI, a friendly HR and recruitment assistant.",
        f"Current job role: {job_role}.",
        "Help with: candidate fit, interview tips, follow-up questions, comparing skills to the role, and scheduling advice.",
        "Be concise, practical, and professional. Use bullet points when listing items.",
    ]
    if analysis:
        lines.append(f"\nCANDIDATE ANALYSIS (JSON):\n{json.dumps(analysis, indent=0)}")
    if questions:
        lines.append(f"\nGENERATED INTERVIEW QUESTIONS:\n{json.dumps(questions[:12], indent=0)}")
    if resume_text:
        lines.append(f"\nRESUME EXCERPT:\n{resume_text[:CHAT_RESUME_EXCERPT]}")
    if not analysis:
        lines.append(
            "\nNo resume analyzed yet. Answer general recruitment questions; "
            "suggest uploading a resume in tab 1 for candidate-specific help."
        )
    return "\n".join(lines)


def chat(
    messages: list[dict],
    job_role: str = "General",
    analysis: dict | None = None,
    questions: list | None = None,
    resume_text: str | None = None,
) -> str:
    """Interactive chat with conversation history."""
    if not messages or messages[-1].get("role") != "user":
        raise ValueError("Last message must be from the user.")

    system_prompt = _build_chat_system_prompt(job_role, analysis, questions, resume_text)
    last_user = messages[-1]["content"]
    history = []
    for msg in messages[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})

    last_err: Exception | None = None
    for model_name in _models_to_try():
        model = _configure_gemini(
            model_name,
            generation_config=CHAT_GENERATION_CONFIG,
            system_instruction=system_prompt,
        )
        for attempt in range(2):
            try:
                session = model.start_chat(history=history)
                response = session.send_message(
                    last_user,
                    request_options={"timeout": 60},
                )
                _mark_model_success(model_name)
                return response.text or "I could not generate a response. Please try again."
            except Exception as e:
                last_err = e
                _mark_model_failed(model_name, e)
                if _is_quota_error(e) and attempt == 0:
                    time.sleep(_retry_seconds(e))
                    continue
                break

    raise ValueError(
        f"Chat unavailable (no working model). Active tried: {get_active_model()}. "
        f"Details: {last_err}"
    ) from last_err
