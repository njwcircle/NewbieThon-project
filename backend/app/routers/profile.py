from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/users/me", tags=["profile"])


def _to_summary(contract: models.Contract) -> schemas.ContractSummaryResponse:
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


@router.get("/contracts", response_model=list[schemas.ContractSummaryResponse])
def list_my_contracts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Contract)
    if current_user.role == models.Role.LANDLORD:
        query = query.filter(models.Contract.landlord_id == current_user.id)
    else:
        query = query.filter(models.Contract.tenant_id == current_user.id)

    contracts = query.order_by(models.Contract.start_date.desc()).all()
    return [_to_summary(c) for c in contracts]


@router.get("/notification-settings", response_model=schemas.NotificationSettingsResponse)
def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    settings = (
        db.query(models.NotificationSettings).filter(models.NotificationSettings.user_id == current_user.id).first()
    )
    if settings is None:
        settings = models.NotificationSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/notification-settings", response_model=schemas.NotificationSettingsResponse)
def update_notification_settings(
    payload: schemas.NotificationSettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    settings = (
        db.query(models.NotificationSettings).filter(models.NotificationSettings.user_id == current_user.id).first()
    )
    if settings is None:
        settings = models.NotificationSettings(user_id=current_user.id)
        db.add(settings)

    settings.payment_alert = payload.payment_alert
    settings.issue_alert = payload.issue_alert
    settings.chat_alert = payload.chat_alert
    db.commit()
    db.refresh(settings)
    return settings
