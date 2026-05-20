from fastapi import APIRouter, HTTPException, status
from backend.models.schemas import UserCreate, UserLogin, Token, UserOut
from backend.auth.jwt_handler import hash_password, verify_password, create_access_token
from backend.services.supabase_client import get_supabase_admin

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    db = get_supabase_admin()
    existing = db.table("users").select("id").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    result = db.table("users").insert({
        "email": user.email,
        "password_hash": hashed,
        "full_name": user.full_name,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Registration failed")
    return result.data[0]


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    db = get_supabase_admin()
    result = db.table("users").select("*").eq("email", credentials.email).execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = result.data[0]
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(token_data=None):
    # token_data injected via dependency in main.py
    db = get_supabase_admin()
    result = db.table("users").select("*").eq("email", token_data.email).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]
