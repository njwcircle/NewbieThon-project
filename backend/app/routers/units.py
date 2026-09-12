from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db, require_landlord

router = APIRouter(prefix="/buildings/{building_id}/units", tags=["units"])


def _get_owned_building(building_id: str, landlord: models.User, db: Session) -> models.Building:
    building = (
        db.query(models.Building)
        .filter(models.Building.id == building_id, models.Building.landlord_id == landlord.id)
        .first()
    )
    if building is None:
        raise HTTPException(status_code=404, detail="건물을 찾을 수 없습니다.")
    return building


@router.post("", response_model=schemas.UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(
    building_id: str,
    payload: schemas.UnitCreateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_building(building_id, landlord, db)

    unit = models.Unit(building_id=building_id, dong=payload.dong, ho=payload.ho)
    db.add(unit)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="이미 등록된 동/호수입니다.") from exc
    db.refresh(unit)
    return unit


@router.get("", response_model=list[schemas.UnitResponse])
def list_units(
    building_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_building(building_id, landlord, db)
    return db.query(models.Unit).filter(models.Unit.building_id == building_id).all()
