from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app import settings
from app.utils.auth import create_access_token

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest):
    if body.username != settings.DEMO_USERNAME or body.password != settings.DEMO_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": body.username})
    return TokenResponse(access_token=token)
