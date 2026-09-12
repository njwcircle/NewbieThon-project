import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def require_landlord(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.Role.LANDLORD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="임대인만 접근 가능합니다.")
    return user


def require_tenant(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.Role.TENANT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="임차인만 접근 가능합니다.")
    return user
