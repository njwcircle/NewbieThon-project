from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db, require_landlord

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.post("", response_model=schemas.BuildingResponse, status_code=status.HTTP_201_CREATED)
def create_building(
    payload: schemas.BuildingCreateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    building = models.Building(landlord_id=landlord.id, address=payload.address)
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


@router.get("", response_model=list[schemas.BuildingResponse])
def list_my_buildings(
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    return db.query(models.Building).filter(models.Building.landlord_id == landlord.id).all()
