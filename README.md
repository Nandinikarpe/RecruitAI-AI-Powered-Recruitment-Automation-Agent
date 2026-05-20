# Recruitment Agent

AI-powered hiring assistant — **Streamlit only** (no separate backend). Analyze resumes with **Google Gemini** (free tier), generate interview questions, schedule interviews, and email the candidate plus HR.

| Layer | Tech |
|-------|------|
| UI | Streamlit |
| AI | Gemini API (`GEMINI_MODEL=auto` picks a working model) |
| Email | SMTP (Gmail App Password recommended) |

## Features

1. **Resume analysis** — skills, experience, strengths, gaps (PDF/DOCX/TXT)
2. **Interview questions** — 5–20 questions tailored to the resume and role
3. **Schedule & notify** — candidate gets interview invite; HR gets full question pack
4. **AI Chat** — interactive assistant about the candidate, interviews, and hiring

## Quick start

### 1. Install dependencies

```bash
cd recruitment-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
```

Edit `.env`:

- `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey) (free)
- `SMTP_USER` / `SMTP_PASSWORD` — Gmail + [App Password](https://myaccount.google.com/apppasswords)
- `HR_EMAIL` — where interview questions are sent

### 3. Run the app

```bash
streamlit run streamlit_app.py
```

Or double-click `run.bat` on Windows.

Open http://localhost:8501

## Workflow

1. **Tab 1** — Upload resume → Analyze → view profile & summary  
2. **Tab 4** — Chat with AI about fit, questions, and interview strategy  
3. **Tab 3** — Review/download HR interview questions  
4. **Tab 2** — Set date/time → Send emails to candidate and HR  

## Streamlit Cloud

Add secrets in the app settings (same keys as `.env`):

- `GEMINI_API_KEY`
- `SMTP_USER`, `SMTP_PASSWORD`, `HR_EMAIL` (optional)

## Email without SMTP

Analysis and questions still work in the UI. Scheduling shows a warning if SMTP is not configured.

## Project structure

```
recruitment-agent/
├── app/
│   ├── config.py
│   ├── models/schemas.py
│   └── services/
│       ├── gemini_service.py
│       ├── resume_parser.py
│       └── email_service.py
├── streamlit_app.py
├── requirements.txt
└── .env.example
```

## Free tier notes (Gemini)

- Set **`GEMINI_MODEL=auto`** (default) — the app lists models from your API key and uses the first that works (e.g. `gemini-2.5-flash-lite`).
- On 429 quota errors it automatically tries the next available model.
- Override with a fixed model: `GEMINI_MODEL=gemini-2.5-flash-lite`
- **One API call** per resume; use **5–8 questions** for faster responses.

## License

MIT
