from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import settings
from app.dal.app_db import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        if email is None:
            raise exc
        return {"email": email, "user_id": user_id}
    except JWTError:
        raise exc


def require_admin(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    from app.dal.user_dal import get_user_by_email, get_user_pages  # local import avoids circular
    user = get_user_by_email(db, current_user["email"])
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    pages = get_user_pages(user)
    if not any(p["slug"] == "admin" for p in pages):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return current_user
