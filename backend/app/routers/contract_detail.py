from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db, require_landlord
from ..utils import effective_payment_status

router = APIRouter(prefix="/contracts", tags=["contract-detail"])


def _get_accessible_contract(contract_id: str, user: models.User, db: Session) -> models.Contract:
    """임대인/임차인 당사자만 이 계약(지난 계약 포함)을 조회할 수 있다."""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    if user.id not in (contract.landlord_id, contract.tenant_id):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return contract


def _to_detail(contract: models.Contract) -> schemas.ContractDetailResponse:
    building = contract.unit.building
    return schemas.ContractDetailResponse(
        id=contract.id,
        building_name=building.name or building.address,
        address=building.address,
        dong=contract.unit.dong,
        ho=contract.unit.ho,
        rent_amount=contract.rent_amount,
        maintenance_fee_fixed=contract.maintenance_fee_fixed,
        start_date=contract.start_date,
        end_date=contract.end_date,
        status=contract.status,
    )


@router.get("/{contract_id}", response_model=schemas.ContractDetailResponse)
def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    contract = _get_accessible_contract(contract_id, current_user, db)
    return _to_detail(contract)


@router.get("/{contract_id}/payments", response_model=list[schemas.PaymentResponse])
def list_payments(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    contract = _get_accessible_contract(contract_id, current_user, db)
    payments = (
        db.query(models.Payment)
        .filter(models.Payment.contract_id == contract.id)
        .order_by(models.Payment.due_date.desc())
        .all()
    )
    return [
        schemas.PaymentResponse(
            id=p.id,
            type=p.type,
            due_date=p.due_date,
            amount=p.amount,
            status=effective_payment_status(p),
            paid_at=p.paid_at,
        )
        for p in payments
    ]


@router.post("/{contract_id}/payments", response_model=schemas.PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    contract_id: str,
    payload: schemas.PaymentCreateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    contract = (
        db.query(models.Contract)
        .filter(models.Contract.id == contract_id, models.Contract.landlord_id == landlord.id)
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")

    payment = models.Payment(
        contract_id=contract.id,
        type=payload.type,
        due_date=payload.due_date,
        amount=payload.amount,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
