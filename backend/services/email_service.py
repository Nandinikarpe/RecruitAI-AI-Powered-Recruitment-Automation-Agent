import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import get_settings

settings = get_settings()


def send_email(to_email: str, subject: str, body: str, html: bool = False) -> bool:
    """Send email via Gmail SMTP. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.gmail_user
        msg["To"] = to_email

        mime_type = "html" if html else "plain"
        msg.attach(MIMEText(body, mime_type))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.gmail_user, settings.gmail_app_password)
            server.sendmail(settings.gmail_user, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[Email Error] {e}")
        return False


def format_html_email(subject: str, body: str, candidate_name: str) -> str:
    """Wrap plain text body in a clean HTML template."""
    paragraphs = "".join(f"<p>{line}</p>" for line in body.split("\n") if line.strip())
    return f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 30px auto; background: white; border-radius: 8px;
                  padding: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background: #4F46E5; color: white; padding: 16px 24px; border-radius: 6px 6px 0 0;
               margin: -32px -32px 24px; }}
    .footer {{ margin-top: 32px; font-size: 12px; color: #888; border-top: 1px solid #eee; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h2 style="margin:0">{subject}</h2></div>
    {paragraphs}
    <div class="footer">This is an automated message from the Recruitment System. Please do not reply directly.</div>
  </div>
</body>
</html>
"""
