from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..chat_service import get_or_create_room
from ..deps import get_current_user, get_db

router = APIRouter(prefix="/contracts/{contract_id}/messages", tags=["chat"])


def _get_accessible_contract(contract_id: str, user: models.User, db: Session) -> models.Contract:
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if contract is None:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다.")
    if user.id not in (contract.landlord_id, contract.tenant_id):
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return contract


def _to_response(message: models.ChatMessage) -> schemas.ChatMessageResponse:
    return schemas.ChatMessageResponse(
        id=message.id,
        type=message.type,
        sender_id=message.sender_id,
        sender_name=message.sender.name if message.sender else None,
        content=message.content,
        ref_id=message.ref_id,
        created_at=message.created_at,
    )


@router.get("", response_model=list[schemas.ChatMessageResponse])
def list_messages(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """일반 메시지/시스템 메시지가 한 타임라인에 섞여서 나온다 — `type`/`sender_id`로 프론트에서 구분해서 렌더링.

    시스템 메시지 중 `type == SYSTEM_ISSUE`는 `ref_id`가 issue_reports.id를 가리키므로,
    카드로 보여주려면 `GET /contracts/{contract_id}/issues`에서 해당 id를 찾아 붙이면 된다.
    """
    _get_accessible_contract(contract_id, current_user, db)
    room = get_or_create_room(db, contract_id)
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.chat_room_id == room.id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    return [_to_response(m) for m in messages]


@router.post("", response_model=schemas.ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    contract_id: str,
    payload: schemas.ChatMessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    contract = _get_accessible_contract(contract_id, current_user, db)
    room = get_or_create_room(db, contract.id)

    message = models.ChatMessage(
        chat_room_id=room.id,
        sender_id=current_user.id,
        type=models.ChatMessageType.TEXT,
        content=payload.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return _to_response(message)
