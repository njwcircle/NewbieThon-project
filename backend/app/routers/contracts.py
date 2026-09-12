from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db, require_landlord

router = APIRouter(prefix="/units/{unit_id}/contracts", tags=["contracts"])


def _get_owned_unit(unit_id: str, landlord: models.User, db: Session) -> models.Unit:
    unit = (
        db.query(models.Unit)
        .join(models.Building)
        .filter(models.Unit.id == unit_id, models.Building.landlord_id == landlord.id)
        .first()
    )
    if unit is None:
        raise HTTPException(status_code=404, detail="호실을 찾을 수 없습니다.")
    return unit


def _get_owned_contract(unit_id: str, contract_id: str, landlord: models.User, db: Session) -> models.Contract:
    contract = (
        db.query(models.Contract)
        .filter(
            models.Contract.id == contract_id,
            models.Contract.unit_id == unit_id,
            models.Contract.landlord_id == landlord.id,
        )
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return contract


@router.post("", response_model=schemas.ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    unit_id: str,
    payload: schemas.ContractCreateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_unit(unit_id, landlord, db)

    contract = models.Contract(
        unit_id=unit_id,
        landlord_id=landlord.id,
        rent_amount=payload.rent_amount,
        maintenance_fee_fixed=payload.maintenance_fee_fixed,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


@router.get("", response_model=list[schemas.ContractResponse])
def list_contracts(
    unit_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_unit(unit_id, landlord, db)
    return db.query(models.Contract).filter(models.Contract.unit_id == unit_id).all()


@router.post("/{contract_id}/invite-code", response_model=schemas.InviteCodeResponse)
def issue_invite_code(
    unit_id: str,
    contract_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    contract = _get_owned_contract(unit_id, contract_id, landlord, db)
    if contract.tenant_id is not None:
        raise HTTPException(status_code=400, detail="이미 임차인이 연결된 계약입니다.")

    invite = models.InviteCode(contract_id=contract.id)
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite
