from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db, require_tenant
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup/landlord",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup_landlord(payload: schemas.LandlordSignupRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="이미 가입된 전화번호입니다.")

    user = models.User(
        role=models.Role.LANDLORD,
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    return schemas.TokenResponse(access_token=token, role=user.role)


@router.post(
    "/signup/tenant",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup_tenant(payload: schemas.TenantSignupRequest, db: Session = Depends(get_db)):
    """초대코드 없이 그냥 일반 가입. 계약 연결은 로그인 후 /auth/redeem-invite-code에서 따로 한다."""
    if db.query(models.User).filter(models.User.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="이미 가입된 전화번호입니다.")

    user = models.User(
        role=models.Role.TENANT,
        name=payload.name,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    return schemas.TokenResponse(access_token=token, role=user.role)


@router.post("/redeem-invite-code", response_model=schemas.ContractSummaryResponse)
def redeem_invite_code(
    payload: schemas.RedeemInviteCodeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_tenant),
):
    """로그인한 임차인이 초대코드를 넣어서 본인 계정을 계약에 연결한다.

    같은 계정으로 여러 계약(예: 재계약, 다른 집으로 이사)을 순차적으로 연결할 수 있다 —
    /users/me/contracts의 "지난 계약" 목록이 바로 이 계정에 연결된 계약들이다.
    """
    invite = db.query(models.InviteCode).filter(models.InviteCode.code == payload.invite_code).first()
    if invite is None:
        raise HTTPException(status_code=404, detail="유효하지 않은 초대코드입니다.")
    if invite.used_at is not None:
        raise HTTPException(status_code=400, detail="이미 사용된 초대코드입니다.")
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="만료된 초대코드입니다.")

    contract = db.query(models.Contract).filter(models.Contract.id == invite.contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="연결된 계약을 찾을 수 없습니다.")
    if contract.tenant_id is not None:
        raise HTTPException(status_code=400, detail="이미 임차인이 연결된 계약입니다.")

    contract.tenant_id = current_user.id
    invite.used_at = datetime.utcnow()
    db.commit()
    db.refresh(contract)

    building = contract.unit.building
    return schemas.ContractSummaryResponse(
        id=contract.id,
        building_name=building.name or building.address,
        dong=contract.unit.dong,
        ho=contract.unit.ho,
        start_date=contract.start_date,
        end_date=contract.end_date,
        status=contract.status,
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.phone == payload.phone).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="전화번호 또는 비밀번호가 올바르지 않습니다.")

    token = create_access_token(subject=user.id, role=user.role.value)
    return schemas.TokenResponse(access_token=token, role=user.role)


@router.get("/me", response_model=schemas.UserResponse)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.patch("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
