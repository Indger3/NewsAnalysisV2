import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dal.app_db import get_db
from app.dal.user_dal import create_user, get_user_by_email, get_user_pages
from app.utils.auth import create_access_token

router = APIRouter(tags=["auth"])

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    email: str
    password: str


class PageInfo(BaseModel):
    slug: str
    label: str
    icon: Optional[str] = None


class UserInfo(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None
    pages: list[PageInfo]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class SignupRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class SignupResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: Optional[str] = None


@router.post("/auth/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    hashed = _pwd_ctx.hash(body.password)
    user = create_user(db, body.email, body.name, hashed)
    return SignupResponse(id=user.id, email=user.email, name=user.name)


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, body.email)

    if not user or not user.is_active or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not _pwd_ctx.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    pages = get_user_pages(user)
    token = create_access_token({"sub": user.email, "user_id": str(user.id)})

    return TokenResponse(
        access_token=token,
        user=UserInfo(
            id=user.id,
            email=user.email,
            name=user.name,
            pages=[PageInfo(**p) for p in pages],
        ),
    )
