# 🤖 RecruitAI — AI-Powered Recruitment Automation Agent

Built with **FastAPI**, **Streamlit**, **Google Gemini**, and **Supabase**.

This repository is a **Python** app (not Next.js). Supabase is used from the backend via the official [`supabase`](https://github.com/supabase/supabase-py) client. You do **not** need `npm install @supabase/supabase-js` unless you add a separate Next.js frontend.

**Python version:** Use **3.11 or 3.12** if you hit build errors installing `pandas` on very new Python releases.

## Features

- 📄 Resume parsing (PDF & DOCX) with automatic info extraction
- 🤖 AI-powered candidate analysis & scoring via Gemini (default **gemini-1.5-flash**, configurable for free tier)
- 📊 HR dashboard with real-time analytics and charts
- 💼 Job posting management
- 👥 Candidate ranking and status tracking
- 📅 Interview scheduling
- 📧 Automated emails (invite / rejection / selection) via Gmail SMTP
- 🔐 JWT authentication

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in your credentials in .env
```

Environment variables are read by `backend/config.py`. You can use either the Python names (`SUPABASE_URL`, `SUPABASE_KEY`, …) or the same names you use in Next.js (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, …). Optional: `GEMINI_MODEL` (default `gemini-1.5-flash`). If `SUPABASE_SERVICE_KEY` is empty, the app uses your publishable/anon key for all DB access (works when RLS is not enabled, as in the bundled schema).

**Secrets:** Never commit `.env`. If a key was pasted into a chat or ticket, rotate it in the Google AI Studio and Supabase dashboards.

### 3. Set up Supabase (connect the database)

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** → New query → paste the full contents of `supabase_schema.sql` → **Run**.  
   This creates tables, the `resumes` storage bucket, indexes, and **turns off RLS** on those tables so the Python backend can read/write using `SUPABASE_KEY` alone.
3. Open **Project Settings → API** and copy into `.env`:
   - **Project URL** → `SUPABASE_URL` (form `https://YOUR_REF.supabase.co`, no trailing slash).
   - **anon public** (legacy JWT starting with `eyJ...`) **or** publishable key → `SUPABASE_KEY`.  
     If the Python client rejects a publishable key, use the **anon** JWT.
   - Optional but recommended for locked-down projects: **service_role** secret → `SUPABASE_SERVICE_KEY` (never expose this in frontend code).
4. Start the API, then verify the connection: **http://localhost:8000/health/supabase**  
   You should see `"connected": true`. If `"connected": false`, read the `detail` and `hint` in the JSON response.

### 4. Configure Gmail SMTP
- Enable 2FA on your Google account
- Generate an App Password at myaccount.google.com/apppasswords
- Add to `.env` as `GMAIL_APP_PASSWORD`

### 5. Get Gemini API Key
- Visit [aistudio.google.com](https://aistudio.google.com)
- Create an API key and add to `.env`

### 6. Run the backend
```bash
cd recruitment-agent
uvicorn backend.main:app --reload --port 8000
```

### 7. Run the frontend (new terminal)
```bash
cd recruitment-agent
streamlit run frontend/app.py
```

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:8501

### Streamlit Community Cloud

Community Cloud may run **Python 3.14**. Older stacks pulled **protobuf 4.x**, which crashes on import (`Metaclasses with custom tp_new are not supported`) before your app loads. This repo pins **`google-generativeai==0.8.6`** and **`protobuf>=5.29,<6`** so Streamlit starts on 3.14.

- Set the app **entrypoint** to `frontend/app.py`.
- If you still see odd protobuf errors, open **App settings → Advanced** and set **Python version** to **3.12**, then redeploy if required.

#### Login & register without hosting FastAPI

If the API is **not** reachable (typical on Cloud), the app uses **Supabase directly** for sign-up and sign-in.

**Streamlit Cloud:** open [share.streamlit.io](https://share.streamlit.io) → your app → **Settings** (⚙) → **Secrets**. Paste this TOML (replace with your values), click **Save**, then **Reboot app**:

```toml
SUPABASE_URL = "https://YOUR_REF.supabase.co"
SUPABASE_KEY = "eyJ...anon JWT from Supabase → Project Settings → API..."
SECRET_KEY = "long-random-string-for-jwt-sessions"
```

See `.streamlit/secrets.toml.example` in the repo. **Do not** rely on `.env` on Cloud — it is not deployed. Secrets must be set in the Streamlit dashboard.

Nested secrets also work:

```toml
[supabase]
url = "https://YOUR_REF.supabase.co"
key = "eyJ..."
SECRET_KEY = "..."
```

**DNS / “Name or service not known”:** `SUPABASE_URL` is wrong or has a typo. Copy **Project URL** exactly from Supabase → **Project Settings → API** (`https://xxxx.supabase.co`).

Run **`supabase_schema.sql`** in the Supabase SQL Editor first (including the RLS-disable section at the bottom) so the `users` table exists.

#### Jobs, AI, uploads, etc.

Those pages still call the **FastAPI** backend. Deploy the API somewhere public and set:

```toml
BACKEND_URL = "https://your-api.example.com"
```

Optional env **`AUTH_VIA_API`**: `true` / `yes` to always use the API for login (fails if it is down); `false` / `no` to always use direct Supabase for login. Default: **auto** (probe `GET /` with a 2s timeout).

## Project Structure

```
recruitment-agent/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings via pydantic-settings
│   ├── auth/
│   │   └── jwt_handler.py   # JWT auth utilities
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── routers/
│   │   ├── auth.py          # Register / Login
│   │   ├── jobs.py          # Job CRUD
│   │   ├── candidates.py    # Resume upload + candidate management
│   │   ├── ai.py            # Gemini analysis, questions, ranking
│   │   ├── interviews.py    # Interview scheduling
│   │   ├── emails.py        # Email automation
│   │   └── analytics.py     # Dashboard stats
│   └── services/
│       ├── supabase_client.py
│       ├── resume_parser.py
│       ├── gemini_service.py
│       └── email_service.py
├── frontend/
│   ├── app.py               # Streamlit entry point
│   ├── components/
│   │   └── sidebar.py
│   ├── pages/
│   │   ├── login_page.py
│   │   ├── dashboard_page.py
│   │   ├── jobs_page.py
│   │   ├── candidates_page.py
│   │   ├── ai_page.py
│   │   ├── interviews_page.py
│   │   └── emails_page.py
│   └── utils/
│       ├── api.py
│       ├── auth.py
│       ├── backend_url.py
│       ├── secrets_bootstrap.py
│       └── supabase_env.py
├── supabase_schema.sql
├── requirements.txt
└── .env.example
```
