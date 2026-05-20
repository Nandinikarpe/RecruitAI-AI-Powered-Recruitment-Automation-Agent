import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import get_settings
from app.models.schemas import InterviewQuestion, ResumeAnalysis


def is_smtp_configured() -> bool:
    settings = get_settings()
    return bool(settings.smtp_user and settings.smtp_password and settings.hr_email)


def smtp_setup_hint() -> str:
    return (
        "**Gmail setup:**\n"
        "1. Turn on [2-Step Verification](https://myaccount.google.com/security)\n"
        "2. Create an [App Password](https://myaccount.google.com/apppasswords) (16 characters)\n"
        "3. In Streamlit Secrets or `.env` set:\n"
        "   - `SMTP_USER` = your full Gmail address\n"
        "   - `SMTP_PASSWORD` = the app password (no spaces)\n"
        "   - `HR_EMAIL` = where HR receives the question pack\n\n"
        "Do **not** use your normal Gmail password."
    )


def _send_email(to: str, subject: str, html_body: str) -> tuple[bool, Optional[str]]:
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        return False, "SMTP_USER and SMTP_PASSWORD are not set."

    user = settings.smtp_user.strip()
    password = settings.smtp_password.replace(" ", "").strip()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to], msg.as_string())
        return True, None
    except smtplib.SMTPAuthenticationError:
        return False, (
            "SMTP authentication failed. For Gmail, use an **App Password** "
            "(not your regular password). Create one at "
            "https://myaccount.google.com/apppasswords after enabling 2-Step Verification."
        )
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except OSError as e:
        return False, f"Could not connect to mail server ({settings.smtp_host}): {e}"
    except Exception as e:
        return False, f"Email failed: {e}"


def _format_questions_html(questions: list[InterviewQuestion]) -> str:
    rows = []
    for i, q in enumerate(questions, 1):
        rationale = f"<br><em>Why: {q.rationale}</em>" if q.rationale else ""
        rows.append(
            f"<li><strong>[{q.category}]</strong> {q.question}{rationale}</li>"
        )
    return "<ol>" + "".join(rows) + "</ol>"


def send_candidate_interview_email(
    candidate_email: str,
    candidate_name: str,
    interview_datetime: datetime,
    interview_mode: str,
    job_role: str,
    meeting_link: Optional[str] = None,
    notes: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    settings = get_settings()
    dt_str = interview_datetime.strftime("%A, %B %d, %Y at %I:%M %p")
    link_block = (
        f'<p><strong>Meeting link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>'
        if meeting_link
        else ""
    )
    notes_block = f"<p><strong>Notes:</strong> {notes}</p>" if notes else ""

    html = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <h2>Interview Invitation — {settings.company_name}</h2>
    <p>Dear {candidate_name},</p>
    <p>Thank you for your application. We would like to invite you for an interview.</p>
    <ul>
      <li><strong>Role:</strong> {job_role}</li>
      <li><strong>Date &amp; Time:</strong> {dt_str}</li>
      <li><strong>Mode:</strong> {interview_mode}</li>
    </ul>
    {link_block}
    {notes_block}
    <p>Please confirm your availability by replying to this email.</p>
    <p>Best regards,<br>{settings.company_name}</p>
    </body></html>
    """
    subject = f"Interview Scheduled — {job_role} | {settings.company_name}"
    return _send_email(candidate_email, subject, html)


def send_hr_interview_pack(
    analysis: ResumeAnalysis,
    questions: list[InterviewQuestion],
    candidate_name: str,
    candidate_email: str,
    interview_datetime: datetime,
    job_role: str,
    interview_mode: str,
    meeting_link: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    settings = get_settings()
    if not settings.hr_email:
        return False, "HR_EMAIL is not set."

    dt_str = interview_datetime.strftime("%A, %B %d, %Y at %I:%M %p")
    skills = ", ".join(analysis.skills[:15]) if analysis.skills else "N/A"
    strengths = ", ".join(analysis.strengths) if analysis.strengths else "N/A"
    link_block = f"<p><strong>Meeting link:</strong> {meeting_link}</p>" if meeting_link else ""

    html = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <h2>Interview Pack — {candidate_name}</h2>
    <h3>Schedule</h3>
    <ul>
      <li><strong>Candidate:</strong> {candidate_name} ({candidate_email})</li>
      <li><strong>Role:</strong> {job_role}</li>
      <li><strong>When:</strong> {dt_str}</li>
      <li><strong>Mode:</strong> {interview_mode}</li>
    </ul>
    {link_block}
    <h3>Resume Summary</h3>
    <p>{analysis.summary}</p>
    <p><strong>Skills:</strong> {skills}</p>
    <p><strong>Experience:</strong> {analysis.experience_years or "N/A"} years</p>
    <p><strong>Strengths:</strong> {strengths}</p>
    <h3>Suggested Interview Questions</h3>
    {_format_questions_html(questions)}
    <p><em>Generated by Recruitment Agent (Gemini).</em></p>
    </body></html>
    """
    subject = f"[HR] Interview Questions — {candidate_name} | {job_role}"
    return _send_email(settings.hr_email.strip(), subject, html)
