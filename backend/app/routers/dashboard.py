from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db, require_landlord
from ..utils import effective_payment_status

router = APIRouter(tags=["dashboard"])


def _build_board_row(unit: models.Unit) -> schemas.BoardRowResponse:
    contract = next((c for c in unit.contracts if c.status == models.ContractStatus.ACTIVE), None)
    if contract is None:
        return schemas.BoardRowResponse(unit_id=unit.id, dong=unit.dong, ho=unit.ho)

    rent_payments = sorted(
        (p for p in contract.payments if p.type == models.PaymentType.RENT),
        key=lambda p: p.due_date,
        reverse=True,
    )
    payment_status = effective_payment_status(rent_payments[0]) if rent_payments else None

    vendor = (
        schemas.RepairVendorResponse.model_validate(contract.assigned_vendor)
        if contract.assigned_vendor is not None
        else None
    )

    return schemas.BoardRowResponse(
        unit_id=unit.id,
        dong=unit.dong,
        ho=unit.ho,
        contract_id=contract.id,
        tenant_name=contract.tenant.name if contract.tenant else None,
        rent_amount=contract.rent_amount,
        maintenance_fee_fixed=contract.maintenance_fee_fixed,
        start_date=contract.start_date,
        end_date=contract.end_date,
        payment_status=payment_status,
        assigned_vendor=vendor,
    )


@router.get("/buildings/{building_id}/board", response_model=list[schemas.BoardRowResponse])
def get_building_board(
    building_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    building = (
        db.query(models.Building)
        .filter(models.Building.id == building_id, models.Building.landlord_id == landlord.id)
        .first()
    )
    if building is None:
        raise HTTPException(status_code=404, detail="건물을 찾을 수 없습니다.")

    return [_build_board_row(unit) for unit in building.units]


@router.get("/users/me/board", response_model=list[schemas.BoardRowResponse])
def get_my_board(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    contracts = (
        db.query(models.Contract)
        .filter(
            models.Contract.tenant_id == current_user.id,
            models.Contract.status == models.ContractStatus.ACTIVE,
        )
        .all()
    )
    return [_build_board_row(c.unit) for c in contracts]


@router.patch("/contracts/{contract_id}/vendor", response_model=schemas.BoardRowResponse)
def assign_vendor(
    contract_id: str,
    payload: schemas.VendorAssignRequest,
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

    if payload.vendor_id is not None:
        vendor = (
            db.query(models.RepairVendor)
            .join(models.Building)
            .filter(models.RepairVendor.id == payload.vendor_id, models.Building.landlord_id == landlord.id)
            .first()
        )
        if vendor is None:
            raise HTTPException(status_code=404, detail="수리업체를 찾을 수 없습니다.")

    contract.assigned_vendor_id = payload.vendor_id
    db.commit()
    db.refresh(contract)
    return _build_board_row(contract.unit)


@router.patch("/payments/{payment_id}/confirm", response_model=schemas.PaymentResponse)
def confirm_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    """납부상태 확인 체크 — 임대인이 입금 확인 후 수동으로 PAID 처리."""
    payment = (
        db.query(models.Payment)
        .join(models.Contract)
        .filter(models.Payment.id == payment_id, models.Contract.landlord_id == landlord.id)
        .first()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="납부 내역을 찾을 수 없습니다.")

    payment.status = models.PaymentStatus.PAID
    payment.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(payment)
    return schemas.PaymentResponse(
        id=payment.id,
        type=payment.type,
        due_date=payment.due_date,
        amount=payment.amount,
        status=effective_payment_status(payment),
        paid_at=payment.paid_at,
    )


@router.get("/notifications/due-payments", response_model=list[schemas.DuePaymentAlertResponse])
def list_due_payment_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """D-3/D-day/연체 대상 조회.

    실제 푸시(FCM)나 카카오 알림톡 발송은 여기서 하지 않는다 — 이 목록을 스케줄러(cron)가
    주기적으로 폴링해서 채팅/푸시로 실제 알림을 내보내는 별도 워커에서 연동해야 한다.
    """
    today = date.today()
    if current_user.role == models.Role.LANDLORD:
        contract_ids = [
            c.id for c in db.query(models.Contract).filter(models.Contract.landlord_id == current_user.id).all()
        ]
    else:
        contract_ids = [
            c.id for c in db.query(models.Contract).filter(models.Contract.tenant_id == current_user.id).all()
        ]

    if not contract_ids:
        return []

    payments = (
        db.query(models.Payment)
        .filter(
            models.Payment.contract_id.in_(contract_ids),
            models.Payment.status != models.PaymentStatus.PAID,
        )
        .all()
    )

    alerts = []
    for payment in payments:
        delta = (payment.due_date - today).days
        if delta == 3:
            alert_type = "D-3"
        elif delta == 0:
            alert_type = "D-DAY"
        elif delta < 0:
            alert_type = "OVERDUE"
        else:
            continue

        contract = payment.contract
        building = contract.unit.building
        alerts.append(
            schemas.DuePaymentAlertResponse(
                payment_id=payment.id,
                contract_id=contract.id,
                building_name=building.name or building.address,
                dong=contract.unit.dong,
                ho=contract.unit.ho,
                due_date=payment.due_date,
                amount=payment.amount,
                type=payment.type,
                alert_type=alert_type,
            )
        )
    return alerts
