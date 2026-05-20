from fastapi import APIRouter, HTTPException, status
from backend.models.schemas import UserCreate, UserLogin, Token, UserOut
from backend.auth.jwt_handler import hash_password, verify_password, create_access_token
from backend.store import get_store

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    store = get_store()
    if store.find_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(user.password)
    row = store.insert_user(user.email, hashed, user.full_name)
    return row


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    store = get_store()
    found = store.find_user_by_email(credentials.email)
    if not found or not verify_password(credentials.password, found["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": found["email"]})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(token_data=None):
    store = get_store()
    found = store.find_user_by_email(token_data.email)
    if not found:
        raise HTTPException(status_code=404, detail="User not found")
    return found
