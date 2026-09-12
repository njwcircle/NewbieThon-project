from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..deps import get_current_user, get_db
from ..legal_service import get_legal_advice

router = APIRouter(prefix="/contracts/{contract_id}/legal-advice", tags=["legal-agent"])


def _get_accessible_contract(contract_id: str, user: models.User, db: Session) -> models.Contract:
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    if user.id not in (contract.landlord_id, contract.tenant_id):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return contract


@router.post("", response_model=schemas.LegalAdviceResponse)
def ask_legal_agent(
    contract_id: str,
    payload: schemas.LegalAdviceRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    contract = _get_accessible_contract(contract_id, current_user, db)
    try:
        return get_legal_advice(db, contract, payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"법률 에이전트 호출 중 오류가 발생했습니다: {exc}") from exc
