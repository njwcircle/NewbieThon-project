from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db, require_landlord

router = APIRouter(prefix="/contracts/{contract_id}/agreements", tags=["agreements"])


def _get_accessible_contract(contract_id: str, user: models.User, db: Session) -> models.Contract:
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    if user.id not in (contract.landlord_id, contract.tenant_id):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return contract


def _get_owned_contract(contract_id: str, landlord: models.User, db: Session) -> models.Contract:
    contract = (
        db.query(models.Contract)
        .filter(models.Contract.id == contract_id, models.Contract.landlord_id == landlord.id)
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    return contract


@router.post("", response_model=schemas.PriorAgreementResponse, status_code=status.HTTP_201_CREATED)
def create_agreement(
    contract_id: str,
    payload: schemas.PriorAgreementCreateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_contract(contract_id, landlord, db)

    agreement = models.PriorAgreement(
        contract_id=contract_id,
        category=payload.category,
        responsible=payload.responsible,
        note=payload.note,
    )
    db.add(agreement)
    db.commit()
    db.refresh(agreement)
    return agreement


@router.get("", response_model=list[schemas.PriorAgreementResponse])
def list_agreements(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_accessible_contract(contract_id, current_user, db)
    return db.query(models.PriorAgreement).filter(models.PriorAgreement.contract_id == contract_id).all()


@router.patch("/{agreement_id}", response_model=schemas.PriorAgreementResponse)
def update_agreement(
    contract_id: str,
    agreement_id: str,
    payload: schemas.PriorAgreementUpdateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_contract(contract_id, landlord, db)
    agreement = (
        db.query(models.PriorAgreement)
        .filter(models.PriorAgreement.id == agreement_id, models.PriorAgreement.contract_id == contract_id)
        .first()
    )
    if agreement is None:
        raise HTTPException(status_code=404, detail="합의사항을 찾을 수 없습니다.")

    agreement.responsible = payload.responsible
    agreement.note = payload.note
    db.commit()
    db.refresh(agreement)
    return agreement


@router.delete("/{agreement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agreement(
    contract_id: str,
    agreement_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_contract(contract_id, landlord, db)
    agreement = (
        db.query(models.PriorAgreement)
        .filter(models.PriorAgreement.id == agreement_id, models.PriorAgreement.contract_id == contract_id)
        .first()
    )
    if agreement is None:
        raise HTTPException(status_code=404, detail="합의사항을 찾을 수 없습니다.")

    db.delete(agreement)
    db.commit()
