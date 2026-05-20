# Recruitment Agent

AI-powered hiring assistant: analyze resumes with **Google Gemini** (free tier), generate tailored interview questions, schedule interviews, and email the candidate plus HR.

| Layer | Tech |
|-------|------|
| API | FastAPI |
| UI | Streamlit |
| AI | Gemini API (`gemini-2.0-flash`) |
| Email | SMTP (Gmail App Password recommended) |

## Features

1. **Resume analysis** — skills, experience, strengths, gaps (PDF/DOCX/TXT)
2. **Interview questions** — 5–20 questions tailored to the resume and role
3. **Schedule & notify** — candidate gets interview invite; HR gets full question pack

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

### 3. Run the API (terminal 1)

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Docs: http://127.0.0.1:8000/docs

### 4. Run Streamlit (terminal 2)

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501

## Workflow

1. **Tab 1** — Upload resume → Analyze → view profile & summary  
2. **Tab 3** — Review/download HR interview questions  
3. **Tab 2** — Set date/time → Send emails to candidate and HR  

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/resume/analyze` | Upload resume → analysis + questions |
| GET | `/api/session/latest` | Last processed session |
| POST | `/api/interview/schedule` | Email candidate + HR (after analyze) |

## Email without SMTP

Analysis and questions still work in the UI. Scheduling returns a warning if SMTP is not configured.

## Project structure

```
recruitment-agent/
├── app/
│   ├── main.py              # FastAPI
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

- Use `gemini-2.0-flash` or `gemini-1.5-flash` for lower cost/rate limits
- Keep resumes under ~12k characters for reliable responses
- If you hit quota errors, wait a minute and retry

## License

MIT
