from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, jobs, candidates, ai, interviews, emails, analytics
from backend.store import get_store

app = FastAPI(
    title="Recruitment Automation Agent",
    description="AI-powered recruitment system using Gemini and local JSON storage",
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


@app.get("/health/store", tags=["Health"])
async def health_store():
    store = get_store()
    return {
        "status": "ok",
        "storage": "json",
        "path": str(store.store_path),
        "counts": store.counts(),
    }
