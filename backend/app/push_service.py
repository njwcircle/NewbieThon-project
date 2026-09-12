"""FCM 발송 래퍼.

로컬 개발: `FIREBASE_CREDENTIALS_PATH`에 서비스 계정 JSON *파일 경로*를 지정.
클라우드 배포: 그 JSON 파일을 git에 올릴 수 없으므로, 파일 내용 전체를 `FIREBASE_CREDENTIALS_JSON`
환경변수에 문자열로 그대로 넣으면 된다 (배포 플랫폼의 "Variables" 설정 화면에 JSON 원문 붙여넣기).
둘 다 없으면 실제 발송 없이 로그만 남기고 조용히 넘어간다 — Firebase 프로젝트 없이도
나머지 기능이 죽지 않게 하려는 것.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

_app = None
_unavailable_reason: str | None = None


def _get_app():
    global _app, _unavailable_reason
    if _app is not None or _unavailable_reason is not None:
        return _app

    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:
        _unavailable_reason = "firebase-admin 패키지 미설치"
        logger.warning("FCM 비활성화: %s", _unavailable_reason)
        return None

    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

    if cred_json:
        try:
            cred = credentials.Certificate(json.loads(cred_json))
        except (json.JSONDecodeError, ValueError):
            _unavailable_reason = "FIREBASE_CREDENTIALS_JSON 파싱 실패 (JSON 형식 확인 필요)"
            logger.warning("FCM 비활성화: %s", _unavailable_reason)
            return None
    elif cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        _unavailable_reason = "FIREBASE_CREDENTIALS_JSON/FIREBASE_CREDENTIALS_PATH 둘 다 미설정"
        logger.warning("FCM 비활성화: %s — 푸시는 로그만 남기고 스킵합니다.", _unavailable_reason)
        return None

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
