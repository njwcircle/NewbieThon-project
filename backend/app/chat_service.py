"""채팅방/시스템 메시지 공용 헬퍼.

다른 기능(예: 문제접수)에서 이 계약의 채팅방에 시스템 메시지를 남기고 싶으면
HTTP를 거치지 않고 이 모듈을 그대로 import해서 post_system_message를 호출하면 된다 —
같은 프로세스, 같은 DB session을 쓰는 모놀리식 백엔드라 이게 제일 간단하다.
"""

from sqlalchemy.orm import Session

from . import models


def get_or_create_room(db: Session, contract_id: str) -> models.ChatRoom:
    room = db.query(models.ChatRoom).filter(models.ChatRoom.contract_id == contract_id).first()
    if room is None:
        room = models.ChatRoom(contract_id=contract_id)
        db.add(room)
        db.commit()
        db.refresh(room)
    return room


def post_system_message(
    db: Session,
    contract_id: str,
    message_type: models.ChatMessageType,
    content: str,
    ref_id: str | None = None,
) -> models.ChatMessage:
    room = get_or_create_room(db, contract_id)
    message = models.ChatMessage(
        chat_room_id=room.id,
        sender_id=None,
        type=message_type,
        content=content,
        ref_id=ref_id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
