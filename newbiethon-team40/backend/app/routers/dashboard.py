from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..chat_service import post_system_message
from ..deps import get_current_user, get_db, require_landlord
from ..utils import effective_payment_status

router = APIRouter(tags=["dashboard"])

PAYMENT_TYPE_LABELS = {
    models.PaymentType.RENT: "월세",
    models.PaymentType.MAINTENANCE_FIXED: "관리비",
    models.PaymentType.MAINTENANCE_VARIABLE: "관리비",
}


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

    label = PAYMENT_TYPE_LABELS[payment.type]
    post_system_message(
        db,
        payment.contract_id,
        models.ChatMessageType.SYSTEM_PAYMENT,
        f"{payment.due_date.month}월 {label}가 납부 완료 처리되었습니다.",
        ref_id=payment.id,
    )

    return schemas.PaymentResponse(
        id=payment.id,
        type=payment.type,
        due_date=payment.due_date,
        amount=payment.amount,
        status=effective_payment_status(payment),
        paid_at=payment.paid_at,
    )


def _alert_type(payment: models.Payment, today: date) -> str | None:
    delta = (payment.due_date - today).days
    if delta == 3:
        return "D-3"
    if delta == 0:
        return "D-DAY"
    if delta < 0:
        return "OVERDUE"
    return None


def _to_alert_response(payment: models.Payment, alert_type: str) -> schemas.DuePaymentAlertResponse:
    contract = payment.contract
    building = contract.unit.building
    return schemas.DuePaymentAlertResponse(
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


@router.get("/notifications/due-payments", response_model=list[schemas.DuePaymentAlertResponse])
def list_due_payment_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """D-3/D-day/연체 대상 미리보기 (본인 관련 계약만) — 채팅에 실제로 메시지를 남기진 않는다."""
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
        alert_type = _alert_type(payment, today)
        if alert_type is not None:
            alerts.append(_to_alert_response(payment, alert_type))
    return alerts


@router.post("/notifications/due-payments/dispatch", response_model=list[schemas.DuePaymentAlertResponse])
def dispatch_due_payment_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """시스템 전체를 훑어서 D-3/D-day/연체 대상마다 해당 계약 채팅방에 시스템 메시지를 실제로 남긴다.

    하루에 같은 (결제건, 알림종류) 조합은 한 번만 남기도록(멱등) 오늘자 채팅 메시지를 먼저 확인한다.
    실제 서비스라면 이 엔드포인트를 하루 한 번 호출하는 스케줄러(cron)가 있어야 하고,
    호출 인증도 사용자 로그인 토큰이 아니라 전용 서비스 자격 증명으로 바꾸는 게 맞다 —
    지금은 그런 스케줄러/서비스 인증 인프라가 없어서 로그인한 사용자 누구나 호출 가능한
    임시 상태다.
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    payments = db.query(models.Payment).filter(models.Payment.status != models.PaymentStatus.PAID).all()

    dispatched = []
    for payment in payments:
        alert_type = _alert_type(payment, today)
        if alert_type is None:
            continue

        marker = f"[{alert_type}]"
        already_sent_today = (
            db.query(models.ChatMessage)
            .filter(
                models.ChatMessage.ref_id == payment.id,
                models.ChatMessage.type == models.ChatMessageType.SYSTEM_PAYMENT,
                models.ChatMessage.content.like(f"{marker}%"),
                models.ChatMessage.created_at >= today_start,
            )
            .first()
        )
        if already_sent_today:
            continue

        label = PAYMENT_TYPE_LABELS[payment.type]
        phrase = {
            "D-3": "3일 남았습니다",
            "D-DAY": "오늘입니다",
            "OVERDUE": "연체되었습니다",
        }[alert_type]
        content = f"{marker} {payment.due_date.month}월 {label} 납부일이 {phrase}"
        post_system_message(db, payment.contract_id, models.ChatMessageType.SYSTEM_PAYMENT, content, ref_id=payment.id)
        dispatched.append(_to_alert_response(payment, alert_type))

    return dispatched
