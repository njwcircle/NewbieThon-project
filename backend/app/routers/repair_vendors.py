from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_db, require_landlord

router = APIRouter(tags=["repair-vendors"])


def _get_owned_building(building_id: str, landlord: models.User, db: Session) -> models.Building:
    building = (
        db.query(models.Building)
        .filter(models.Building.id == building_id, models.Building.landlord_id == landlord.id)
        .first()
    )
    if building is None:
        raise HTTPException(status_code=404, detail="건물을 찾을 수 없습니다.")
    return building


def _get_owned_vendor(vendor_id: str, landlord: models.User, db: Session) -> models.RepairVendor:
    vendor = (
        db.query(models.RepairVendor)
        .join(models.Building)
        .filter(models.RepairVendor.id == vendor_id, models.Building.landlord_id == landlord.id)
        .first()
    )
    if vendor is None:
        raise HTTPException(status_code=404, detail="수리업체를 찾을 수 없습니다.")
    return vendor


@router.post(
    "/buildings/{building_id}/repair-vendors",
    response_model=schemas.RepairVendorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vendor(
    building_id: str,
    payload: schemas.RepairVendorCreateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_building(building_id, landlord, db)

    vendor = models.RepairVendor(
        building_id=building_id,
        category=payload.category,
        name=payload.name,
        phone=payload.phone,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/buildings/{building_id}/repair-vendors", response_model=list[schemas.RepairVendorResponse])
def list_vendors(
    building_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    _get_owned_building(building_id, landlord, db)
    return db.query(models.RepairVendor).filter(models.RepairVendor.building_id == building_id).all()


@router.patch("/repair-vendors/{vendor_id}", response_model=schemas.RepairVendorResponse)
def update_vendor(
    vendor_id: str,
    payload: schemas.RepairVendorUpdateRequest,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    vendor = _get_owned_vendor(vendor_id, landlord, db)
    vendor.category = payload.category
    vendor.name = payload.name
    vendor.phone = payload.phone
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/repair-vendors/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    landlord: models.User = Depends(require_landlord),
):
    vendor = _get_owned_vendor(vendor_id, landlord, db)
    db.delete(vendor)
    db.commit()
