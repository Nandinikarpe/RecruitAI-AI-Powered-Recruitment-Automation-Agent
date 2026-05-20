from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import get_settings
from backend.routers import auth, jobs, candidates, ai, interviews, emails, analytics
from backend.services.supabase_client import get_supabase_admin

app = FastAPI(
    title="Recruitment Automation Agent",
    description="AI-powered recruitment system using Gemini, Supabase, and Gmail",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(candidates.router)
app.include_router(ai.router)
app.include_router(interviews.router)
app.include_router(emails.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Recruitment Agent API is running"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/health/supabase", tags=["Health"])
def health_supabase():
    """
    Verifies `.env` Supabase URL/key and that the `users` table is reachable via PostgREST.
    Open in the browser or curl after starting the API.
    """
    try:
        db = get_supabase_admin()
        res = db.table("users").select("id").limit(1).execute()
        err = getattr(res, "error", None)
        if err is not None:
            return JSONResponse(
                status_code=503,
                content={"connected": False, "detail": str(err)},
            )
        cfg = get_settings()
        using_service = bool((cfg.supabase_service_key or "").strip())
        return {
            "connected": True,
            "using_service_role_key": using_service,
            "hint": "If registration still fails, re-run the full `supabase_schema.sql` in the SQL Editor "
            "and confirm `SUPABASE_URL` / `SUPABASE_KEY` match Project Settings → API.",
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "connected": False,
                "detail": str(e),
                "hint": "Use the anon (legacy JWT) or publishable key as SUPABASE_KEY, or set "
                "SUPABASE_SERVICE_KEY to the service_role secret. Ensure the URL is "
                "https://<ref>.supabase.co with no trailing slash.",
            },
        )
