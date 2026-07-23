from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from core.security import create_access_token
from services.auth_service import authenticate_user, create_user, get_current_user
from schemas.auth import RegisterRequest, LoginRequest, MeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(data: RegisterRequest):
    username = data.username.strip()
    password = data.password

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = create_user(username, data.email, password)
    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "username": user["username"],
            "email": user["email"],
        },
    )


@router.post("/login")
async def login(data: LoginRequest):
    username = data.username.strip()

    user = authenticate_user(username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(
        {"sub": str(user["id"]), "username": user["username"]},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
    }


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    return MeResponse(user_id=current_user["user_id"], username=current_user["username"])