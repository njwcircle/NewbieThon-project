"""채팅방/시스템 메시지 공용 헬퍼.

다른 기능(예: 문제접수)에서 이 계약의 채팅방에 시스템 메시지를 남기고 싶으면
HTTP를 거치지 않고 이 모듈을 그대로 import해서 post_system_message를 호출하면 된다 —
같은 프로세스, 같은 DB session을 쓰는 모놀리식 백엔드라 이게 제일 간단하다.

메시지가 남을 때마다 관련 당사자에게 FCM 푸시도 같이 나간다(push_service 경유).
Firebase가 설정 안 돼 있으면 push_service가 알아서 스킵하니 여기서는 신경 안 써도 된다.
"""

from sqlalchemy.orm import Session

from . import models, push_service

_ALERT_FIELD_BY_MESSAGE_TYPE = {
    models.ChatMessageType.SYSTEM_PAYMENT: "payment_alert",
    models.ChatMessageType.SYSTEM_ISSUE: "issue_alert",
    models.ChatMessageType.TEXT: "chat_alert",
}


def get_or_create_room(db: Session, contract_id: str) -> models.ChatRoom:
    room = db.query(models.ChatRoom).filter(models.ChatRoom.contract_id == contract_id).first()
    if room is None:
        room = models.ChatRoom(contract_id=contract_id)
        db.add(room)
        db.commit()
        db.refresh(room)
    return room


def _notification_enabled(db: Session, user_id: str, message_type: models.ChatMessageType) -> bool:
    field = _ALERT_FIELD_BY_MESSAGE_TYPE[message_type]
    settings = db.query(models.NotificationSettings).filter(models.NotificationSettings.user_id == user_id).first()
    if settings is None:
        return True  # 설정 안 했으면 기본값(전부 on)과 동일하게 취급
    return getattr(settings, field)


def _device_tokens(db: Session, user_id: str) -> list[str]:
    return [t.token for t in db.query(models.DeviceToken).filter(models.DeviceToken.user_id == user_id).all()]


def _push_to_recipients(
    db: Session,
    recipient_ids: list[str | None],
    message_type: models.ChatMessageType,
    title: str,
    body: str,
    contract_id: str,
    ref_id: str | None,
) -> None:
    tokens: list[str] = []
    for user_id in recipient_ids:
        if user_id is None:
            continue
        if not _notification_enabled(db, user_id, message_type):
            continue
        tokens.extend(_device_tokens(db, user_id))

    data = {"contract_id": contract_id, "type": message_type.value}
    if ref_id is not None:
        data["ref_id"] = ref_id
    push_service.send_push(tokens, title, body, data=data)


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

    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if contract is not None:
        _push_to_recipients(
            db,
            [contract.landlord_id, contract.tenant_id],
            message_type,
            title="알림",
            body=content,
            contract_id=contract_id,
            ref_id=ref_id,
        )
    return message


def post_text_message(db: Session, contract: models.Contract, sender: models.User, content: str) -> models.ChatMessage:
    room = get_or_create_room(db, contract.id)
    message = models.ChatMessage(
        chat_room_id=room.id,
        sender_id=sender.id,
        type=models.ChatMessageType.TEXT,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    other_party_id = contract.tenant_id if sender.id == contract.landlord_id else contract.landlord_id
    _push_to_recipients(
        db,
        [other_party_id],
        models.ChatMessageType.TEXT,
        title=sender.name,
        body=content,
        contract_id=contract.id,
        ref_id=None,
    )
    return message
