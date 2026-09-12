from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/users/me/device-tokens", tags=["push"])


@router.post("", response_model=schemas.DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
def register_device_token(
    payload: schemas.DeviceTokenRegisterRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """같은 토큰이 이미 등록돼 있으면(재설치/재로그인) 소유자를 현재 사용자로 갱신(upsert)."""
    token = db.query(models.DeviceToken).filter(models.DeviceToken.token == payload.token).first()
    if token is None:
        token = models.DeviceToken(token=payload.token, user_id=current_user.id, platform=payload.platform)
        db.add(token)
    else:
        token.user_id = current_user.id
        token.platform = payload.platform
    db.commit()
    db.refresh(token)
    return token


@router.get("", response_model=list[schemas.DeviceTokenResponse])
def list_device_tokens(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.DeviceToken).filter(models.DeviceToken.user_id == current_user.id).all()


@router.delete("/{token_value}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device_token(
    token_value: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """로그아웃 시 호출 — 이 기기로는 더 이상 푸시를 받지 않게 함."""
    token = (
        db.query(models.DeviceToken)
        .filter(models.DeviceToken.token == token_value, models.DeviceToken.user_id == current_user.id)
        .first()
    )
    if token is None:
        raise HTTPException(status_code=404, detail="등록된 디바이스 토큰을 찾을 수 없습니다.")
    db.delete(token)
    db.commit()
