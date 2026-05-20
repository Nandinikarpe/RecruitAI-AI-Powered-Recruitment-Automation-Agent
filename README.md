# 🤖 RecruitAI — AI-Powered Recruitment Automation Agent

Built with **FastAPI**, **Streamlit**, and **Google Gemini**. **No external database** — data is stored in local JSON files under `data/`.

**Python version:** Use **3.11 or 3.12** if you hit build errors installing `pandas` on very new Python releases.

## Features

- 📄 Resume parsing (PDF & DOCX) with automatic info extraction
- 🤖 AI-powered candidate analysis & scoring via Gemini (default **gemini-1.5-flash**)
- 📊 HR dashboard with analytics and charts
- 💼 Job posting management
- 👥 Candidate ranking and status tracking
- 📅 Interview scheduling
- 📧 Automated emails via Gmail SMTP (optional)
- 🔐 JWT authentication

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY and SECRET_KEY at minimum
```

Required:
- `GEMINI_API_KEY` — from [aistudio.google.com](https://aistudio.google.com)
- `SECRET_KEY` — long random string for login sessions

Optional:
- `GMAIL_USER` / `GMAIL_APP_PASSWORD` — for email features
- `DATA_DIR` — where JSON data is saved (default: `data/`)

### 3. Run the backend
```bash
uvicorn backend.main:app --reload --port 8000
```

Health check: http://localhost:8000/health/store

### 4. Run the frontend (new terminal)
```bash
streamlit run frontend/app.py
```

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:8501

## Storage (no database)

All data lives in **`data/store.json`** (users, jobs, candidates, interviews, etc.). Uploaded resumes are saved under **`data/resumes/`**.

- No Supabase, PostgreSQL, or other external DB required
- On **Streamlit Cloud**, the filesystem is ephemeral — data may reset when the app redeploys unless you host the API on a server with persistent disk

## Streamlit Community Cloud

Set **entrypoint** to `frontend/app.py`.

**Secrets** (Settings → Secrets):

```toml
SECRET_KEY = "long-random-string"
GEMINI_API_KEY = "your-gemini-key"
```

Login/register works **without** a separate API — accounts are saved to `data/store.json` on the Cloud machine.

For jobs, candidates, AI, etc., either:
- Run the **FastAPI backend** locally and set `BACKEND_URL`, or
- Deploy the API (Railway, Render, etc.) and set `BACKEND_URL` in Streamlit secrets

Optional: `AUTH_VIA_API=false` forces local JSON auth; `true` forces API auth.

## Project Structure

```
recruitment-agent/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── store/
│   │   └── json_store.py    # Local JSON persistence
│   ├── auth/
│   ├── models/
│   ├── routers/
│   └── services/
├── frontend/
│   ├── app.py
│   ├── pages/
│   └── utils/
├── data/                    # Created at runtime (gitignored)
├── requirements.txt
└── .env.example
```
