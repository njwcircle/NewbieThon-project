"""FCM 발송 래퍼.

`FIREBASE_CREDENTIALS_PATH` 환경변수가 없거나 파일이 없으면 실제 발송 없이 로그만 남기고
조용히 넘어간다 — 로컬 개발/CI에서 진짜 Firebase 프로젝트 없이도 나머지 기능이 죽지 않게 하려는 것.
실제 서비스 배포 시에는 Firebase 콘솔에서 발급한 서비스 계정 JSON 경로를 이 환경변수에 설정하면 된다.
"""

import logging
import os

logger = logging.getLogger(__name__)

_app = None
_unavailable_reason: str | None = None


def _get_app():
    global _app, _unavailable_reason
    if _app is not None or _unavailable_reason is not None:
        return _app

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    if not cred_path or not os.path.exists(cred_path):
        _unavailable_reason = "FIREBASE_CREDENTIALS_PATH 미설정 또는 파일 없음"
        logger.warning("FCM 비활성화: %s — 푸시는 로그만 남기고 스킵합니다.", _unavailable_reason)
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        _unavailable_reason = "firebase-admin 패키지 미설치"
        logger.warning("FCM 비활성화: %s", _unavailable_reason)
        return None

    cred = credentials.Certificate(cred_path)
    _app = firebase_admin.initialize_app(cred)
    return _app


def send_push(tokens: list[str], title: str, body: str, data: dict | None = None) -> None:
    """tokens가 비어있으면 아무것도 안 하고, Firebase 미설정이면 로그만 남기고 스킵."""
    if not tokens:
        return

    app = _get_app()
    if app is None:
        logger.info("[FCM skip] title=%r body=%r tokens=%d개", title, body, len(tokens))
        return

    from firebase_admin import messaging

    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data={k: str(v) for k, v in (data or {}).items()},
        tokens=tokens,
    )
    try:
        response = messaging.send_each_for_multicast(message, app=app)
        logger.info("FCM 발송 완료: success=%d failure=%d", response.success_count, response.failure_count)
    except Exception:
        logger.exception("FCM 발송 실패")
