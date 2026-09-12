"""시연용 데모 데이터 시드 스크립트.

로컬(uvicorn 켜둔 상태)이든 Railway 배포 주소든 상관없이 실행 가능:

    python seed_demo.py                                   # 기본값: http://127.0.0.1:8000
    python seed_demo.py https://xxxx.up.railway.app        # 배포 주소 대상

여러 번 실행해도 안전함(idempotent) — 이미 가입된 계정이면 로그인만 하고,
이미 있는 건물/계약이면 새로 안 만들고 재사용함. 재배포로 DB가 초기화된 뒤에도
그냥 다시 실행하면 됨.

외부 패키지 없이 표준 라이브러리(urllib)만 사용 — pip install 없이 바로 실행 가능.
"""

import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

# Windows 콘솔 기본 코드페이지(cp949)에서 "—" 같은 문자를 print()하면 죽는 걸 방지.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"

LANDLORD = {"name": "박집주인", "phone": "01000000001", "password": "demo1234!"}
TENANT = {"name": "김세입자", "phone": "01000000002", "password": "demo1234!"}
BUILDING = {"name": "고려빌라", "address": "서울시 성북구 안암동 123-45"}
UNIT = {"dong": "101", "ho": "202"}
CONTRACT = {
    "rent_amount": 550000,
    "maintenance_fee_fixed": 50000,
    "start_date": "2026-01-01",
    "end_date": "2027-01-01",
}
VENDOR = {"category": "BOILER", "name": "고려보일러", "phone": "02-123-4567"}


def call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, (json.loads(raw) if raw else {})


def log(msg: str) -> None:
    print(f"  {msg}")


def signup_or_login(role: str, info: dict) -> str:
    """이미 가입돼 있으면 로그인, 아니면 새로 가입. 토큰을 반환."""
    status, data = call("POST", f"/auth/signup/{role}", {k: info[k] for k in ("name", "phone", "password")})
    if status == 201:
        log(f"{info['name']} 신규 가입 완료")
        return data["access_token"]

    status, data = call("POST", "/auth/login", {"phone": info["phone"], "password": info["password"]})
    if status != 200:
        raise RuntimeError(f"{info['name']} 로그인 실패: {status} {data}")
    log(f"{info['name']} 이미 존재 — 로그인만 함")
    return data["access_token"]


def get_or_create_building(token: str) -> str:
    status, buildings = call("GET", "/buildings", token=token)
    for b in buildings:
        if b["address"] == BUILDING["address"]:
            log(f"건물 '{b['name']}' 이미 있음 — 재사용")
            return b["id"]

    status, data = call("POST", "/buildings", BUILDING, token=token)
    if status != 201:
        raise RuntimeError(f"건물 생성 실패: {status} {data}")
    log(f"건물 '{BUILDING['name']}' 생성")
    return data["id"]


def get_or_create_unit(token: str, building_id: str) -> str:
    status, units = call("GET", f"/buildings/{building_id}/units", token=token)
    for u in units:
        if u["dong"] == UNIT["dong"] and u["ho"] == UNIT["ho"]:
            log(f"호실 {u['dong']}동 {u['ho']}호 이미 있음 — 재사용")
            return u["id"]

    status, data = call("POST", f"/buildings/{building_id}/units", UNIT, token=token)
    if status != 201:
        raise RuntimeError(f"호실 생성 실패: {status} {data}")
    log(f"호실 {UNIT['dong']}동 {UNIT['ho']}호 생성")
    return data["id"]


def get_or_create_contract(token: str, unit_id: str) -> str:
    status, contracts = call("GET", f"/units/{unit_id}/contracts", token=token)
    if contracts:
        log("계약 이미 있음 — 재사용")
        return contracts[0]["id"]

    status, data = call("POST", f"/units/{unit_id}/contracts", CONTRACT, token=token)
    if status != 201:
        raise RuntimeError(f"계약 생성 실패: {status} {data}")
    log("계약 생성")
    return data["id"]


def ensure_tenant_linked(landlord_token: str, tenant_token: str, unit_id: str, contract_id: str) -> None:
    status, contract = call("GET", f"/contracts/{contract_id}", token=tenant_token)
    if status == 200:
        log("임차인 이미 이 계약에 연결됨")
        return

    status, data = call(
        "POST", f"/units/{unit_id}/contracts/{contract_id}/invite-code", token=landlord_token
    )
    if status != 200:
        raise RuntimeError(f"초대코드 발급 실패: {status} {data}")
    invite_code = data["code"]

    status, data = call("POST", "/auth/redeem-invite-code", {"invite_code": invite_code}, token=tenant_token)
    if status != 200:
        raise RuntimeError(f"초대코드 연결 실패: {status} {data}")
    log("초대코드로 임차인-계약 연결 완료")


def ensure_vendor(landlord_token: str, building_id: str) -> str:
    status, vendors = call("GET", f"/buildings/{building_id}/repair-vendors", token=landlord_token)
    for v in vendors:
        if v["name"] == VENDOR["name"]:
            return v["id"]

    status, data = call("POST", f"/buildings/{building_id}/repair-vendors", VENDOR, token=landlord_token)
    if status != 201:
        raise RuntimeError(f"수리업체 등록 실패: {status} {data}")
    log(f"수리업체 '{VENDOR['name']}' 등록")
    return data["id"]


def ensure_agreement(landlord_token: str, contract_id: str) -> None:
    status, agreements = call("GET", f"/contracts/{contract_id}/agreements", token=landlord_token)
    if any(a["category"] == "BOILER" for a in agreements):
        log("사전합의사항 이미 있음")
        return

    status, data = call(
        "POST",
        f"/contracts/{contract_id}/agreements",
        {"category": "BOILER", "responsible": "LANDLORD", "note": "노후 보일러 고장은 임대인 부담"},
        token=landlord_token,
    )
    if status != 201:
        raise RuntimeError(f"사전합의사항 등록 실패: {status} {data}")
    log("사전합의사항 등록 (보일러 -> 임대인 부담)")


def ensure_vendor_assigned(landlord_token: str, contract_id: str, vendor_id: str) -> None:
    call("PATCH", f"/contracts/{contract_id}/vendor", {"vendor_id": vendor_id}, token=landlord_token)
    log("계약에 수리업체 배정")


def ensure_payments(landlord_token: str, contract_id: str) -> None:
    status, payments = call("GET", f"/contracts/{contract_id}/payments", token=landlord_token)
    if payments:
        log(f"납부 항목 이미 {len(payments)}건 있음 — 스킵")
        return

    today = date.today()
    to_create = [
        # 지난달 월세: 이미 확인 처리(PAID) -> 채팅에 "납부 완료" 시스템 메시지 남김
        {"type": "RENT", "due_date": (today - timedelta(days=25)).isoformat(), "amount": CONTRACT["rent_amount"], "confirm": True},
        # 이번달 월세: 연체(과거 날짜, 미확인) -> 대시보드에 OVERDUE로 보임
        {"type": "RENT", "due_date": (today - timedelta(days=3)).isoformat(), "amount": CONTRACT["rent_amount"], "confirm": False},
        # 다음 관리비: D-3 -> 알림 데모용
        {"type": "MAINTENANCE_FIXED", "due_date": (today + timedelta(days=3)).isoformat(), "amount": CONTRACT["maintenance_fee_fixed"], "confirm": False},
    ]
    for p in to_create:
        status, data = call(
            "POST",
            f"/contracts/{contract_id}/payments",
            {"type": p["type"], "due_date": p["due_date"], "amount": p["amount"]},
            token=landlord_token,
        )
        if status != 201:
            raise RuntimeError(f"납부 항목 생성 실패: {status} {data}")
        if p["confirm"]:
            call("PATCH", f"/payments/{data['id']}/confirm", token=landlord_token)
    log("납부 항목 3건 생성 (완료 1 / 연체 1 / D-3 예정 1)")


def ensure_issues(landlord_token: str, tenant_token: str, contract_id: str) -> None:
    status, issues = call("GET", f"/contracts/{contract_id}/issues", token=tenant_token)
    if issues:
        log(f"문제접수 이미 {len(issues)}건 있음 — 스킵")
        return

    # 1) 사전합의 있는 카테고리 -> 자동 판정 + 임대인이 해결 처리까지 완료
    status, data = call(
        "POST",
        f"/contracts/{contract_id}/issues",
        {"category": "BOILER", "description": "새벽에 보일러에서 이상한 소리가 나고 온수가 안 나와요."},
        token=tenant_token,
    )
    if status == 201:
        issue_id = data["issue"]["id"]
        call(
            "POST",
            f"/contracts/{contract_id}/issues/{issue_id}/resolve",
            {
                "resolver": "REPAIR_VENDOR",
                "resolved_detail": "고려보일러 출동, 순환펌프 교체",
                "cost": 85000,
                "payer": "LANDLORD",
                "payment_status": "PAID",
            },
            token=landlord_token,
        )
        log("문제접수 1건 등록 + 해결 처리 완료 (보일러, 사전합의 자동매칭)")

    # 2) 사전합의 없는 카테고리 -> 채팅으로 넘어간 상태 그대로 둠 (협의중 예시)
    status, data = call(
        "POST",
        f"/contracts/{contract_id}/issues",
        {"category": "FURNITURE", "description": "붙박이장 문이 떨어졌어요. 사진 첨부할게요."},
        token=tenant_token,
    )
    if status == 201:
        log("문제접수 1건 등록 (가구, 사전합의 없음 -> 채팅 협의중 상태)")


def ensure_chat(landlord_token: str, tenant_token: str, contract_id: str) -> None:
    status, messages = call("GET", f"/contracts/{contract_id}/messages", token=tenant_token)
    text_messages = [m for m in messages if m["type"] == "TEXT"]
    if text_messages:
        log(f"일반 채팅 메시지 이미 {len(text_messages)}건 있음 — 스킵")
        return

    conversation = [
        (tenant_token, "안녕하세요, 붙박이장 문이 떨어져서 연락드려요. 사진은 이따 올려드릴게요."),
        (landlord_token, "네 확인했습니다! 사전에 합의된 항목이 아니라 한번 같이 상황 볼게요."),
        (tenant_token, "네 감사합니다 :)"),
    ]
    for token, content in conversation:
        call("POST", f"/contracts/{contract_id}/messages", {"content": content}, token=token)
    log("일반 채팅 메시지 3건 등록")


def ensure_notification_settings(tenant_token: str) -> None:
    call(
        "PUT",
        "/users/me/notification-settings",
        {"payment_alert": True, "issue_alert": True, "chat_alert": True},
        token=tenant_token,
    )


def main() -> None:
    print(f"대상 서버: {BASE_URL}\n")

    status, _ = call("GET", "/health")
    if status != 200:
        raise SystemExit(f"서버가 응답하지 않습니다 ({BASE_URL}/health -> {status}). 서버가 켜져 있는지 확인하세요.")

    print("[1/8] 계정 준비")
    landlord_token = signup_or_login("landlord", LANDLORD)
    tenant_token = signup_or_login("tenant", TENANT)

    print("[2/8] 건물/호실/계약")
    building_id = get_or_create_building(landlord_token)
    unit_id = get_or_create_unit(landlord_token, building_id)
    contract_id = get_or_create_contract(landlord_token, unit_id)

    print("[3/8] 임차인-계약 연결")
    ensure_tenant_linked(landlord_token, tenant_token, unit_id, contract_id)

    print("[4/8] 수리업체 + 사전합의사항")
    vendor_id = ensure_vendor(landlord_token, building_id)
    ensure_agreement(landlord_token, contract_id)
    ensure_vendor_assigned(landlord_token, contract_id, vendor_id)

    print("[5/8] 납부 내역")
    ensure_payments(landlord_token, contract_id)

    print("[6/8] 문제접수")
    ensure_issues(landlord_token, tenant_token, contract_id)

    print("[7/8] 채팅")
    ensure_chat(landlord_token, tenant_token, contract_id)

    print("[8/8] 알림설정")
    ensure_notification_settings(tenant_token)

    print(
        f"""
데모 데이터 준비 완료!

로그인 정보
  임대인: {LANDLORD['phone']} / {LANDLORD['password']} ({LANDLORD['name']})
  임차인: {TENANT['phone']} / {TENANT['password']} ({TENANT['name']})

건물/계약: {BUILDING['name']} {UNIT['dong']}동 {UNIT['ho']}호 (contract_id={contract_id})

보여줄 수 있는 것
  - 대시보드 보드: 세입자명/월세/납부상태(연체 1건 포함)/배정된 수리업체
  - 채팅: 일반 대화 3건 + 시스템 메시지(납부 완료, 문제접수/해결) 자동 표시
  - 문제접수: 해결 완료 1건(보일러) + 협의중 1건(가구)
  - 알림: GET /notifications/due-payments 로 D-3 관리비 확인 가능
"""
    )


if __name__ == "__main__":
    main()
