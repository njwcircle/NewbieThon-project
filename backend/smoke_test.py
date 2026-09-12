"""One-off smoke test for the login/building/unit/contract flow. Not a permanent test file."""

import os
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./smoke_test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def expect(condition, message):
    if not condition:
        raise AssertionError(message)


# 1. landlord signup
r = client.post(
    "/auth/signup/landlord",
    json={"name": "집주인", "phone": "01011112222", "password": "password123"},
)
expect(r.status_code == 201, f"landlord signup failed: {r.status_code} {r.text}")
landlord_token = r.json()["access_token"]
landlord_headers = {"Authorization": f"Bearer {landlord_token}"}
print("landlord signup OK")

# 2. create building
r = client.post(
    "/buildings",
    json={"name": "고려빌라", "address": "서울시 어딘가 101동"},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create building failed: {r.status_code} {r.text}")
building_id = r.json()["id"]
print("building create OK", building_id)

# 3. create unit
r = client.post(
    f"/buildings/{building_id}/units",
    json={"dong": "101", "ho": "202"},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create unit failed: {r.status_code} {r.text}")
unit_id = r.json()["id"]
print("unit create OK", unit_id)

# 3b. duplicate unit should fail
r = client.post(
    f"/buildings/{building_id}/units",
    json={"dong": "101", "ho": "202"},
    headers=landlord_headers,
)
expect(r.status_code == 400, f"duplicate unit should fail: {r.status_code} {r.text}")
print("duplicate unit rejected OK")

# 4. create contract
r = client.post(
    f"/units/{unit_id}/contracts",
    json={
        "rent_amount": 500000,
        "maintenance_fee_fixed": 50000,
        "start_date": "2026-01-01",
        "end_date": "2027-01-01",
    },
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create contract failed: {r.status_code} {r.text}")
contract_id = r.json()["id"]
print("contract create OK", contract_id)

# 5. issue invite code
r = client.post(f"/units/{unit_id}/contracts/{contract_id}/invite-code", headers=landlord_headers)
expect(r.status_code == 200, f"issue invite code failed: {r.status_code} {r.text}")
invite_code = r.json()["code"]
print("invite code issued OK", invite_code)

# 6. tenant signup with invite code
r = client.post(
    "/auth/signup/tenant",
    json={
        "invite_code": invite_code,
        "name": "세입자",
        "phone": "01033334444",
        "password": "password123",
    },
)
expect(r.status_code == 201, f"tenant signup failed: {r.status_code} {r.text}")
tenant_token = r.json()["access_token"]
tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
print("tenant signup OK")

# 6b. reusing the same invite code should fail
r = client.post(
    "/auth/signup/tenant",
    json={
        "invite_code": invite_code,
        "name": "다른사람",
        "phone": "01055556666",
        "password": "password123",
    },
)
expect(r.status_code == 400, f"reused invite code should fail: {r.status_code} {r.text}")
print("reused invite code rejected OK")

# 7. login as landlord
r = client.post("/auth/login", json={"phone": "01011112222", "password": "password123"})
expect(r.status_code == 200, f"landlord login failed: {r.status_code} {r.text}")
print("landlord login OK")

# 8. /auth/me for both roles
r = client.get("/auth/me", headers=landlord_headers)
expect(r.status_code == 200 and r.json()["role"] == "LANDLORD", f"landlord /me failed: {r.text}")
print("landlord /me OK")

r = client.get("/auth/me", headers=tenant_headers)
expect(r.status_code == 200 and r.json()["role"] == "TENANT", f"tenant /me failed: {r.text}")
print("tenant /me OK")

# 9. tenant should be forbidden from creating buildings
r = client.post("/buildings", json={"address": "임차인이 만들면 안됨"}, headers=tenant_headers)
expect(r.status_code == 403, f"tenant building create should be forbidden: {r.status_code} {r.text}")
print("tenant forbidden from building create OK")

# 10. wrong password
r = client.post("/auth/login", json={"phone": "01011112222", "password": "wrongpassword"})
expect(r.status_code == 401, f"wrong password should fail: {r.status_code} {r.text}")
print("wrong password rejected OK")

# --- 프로필 기능 ---

# 11. tenant's 지난 계약 목록 (건물명 + 호실 표시)
r = client.get("/users/me/contracts", headers=tenant_headers)
expect(r.status_code == 200, f"tenant contracts list failed: {r.status_code} {r.text}")
contracts = r.json()
expect(len(contracts) == 1, f"tenant should have exactly 1 contract: {contracts}")
expect(
    contracts[0]["building_name"] == "고려빌라" and contracts[0]["ho"] == "202",
    f"contract summary mismatch: {contracts[0]}",
)
print("tenant 지난 계약 list OK")

# 11b. landlord도 같은 계약을 자기 목록에서 봐야 함
r = client.get("/users/me/contracts", headers=landlord_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"landlord contracts list failed: {r.text}")
print("landlord 지난 계약 list OK")

# 12. 계약 정보 상세 (당사자만 조회 가능)
r = client.get(f"/contracts/{contract_id}", headers=tenant_headers)
expect(r.status_code == 200 and r.json()["rent_amount"] == 500000, f"contract detail failed: {r.text}")
print("contract detail OK")

# 12b. 제3자(가입만 되어있고 이 계약과 무관한 사용자)는 조회 불가
r = client.post(
    "/auth/signup/landlord",
    json={"name": "관계없는사람", "phone": "01099998888", "password": "password123"},
)
stranger_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
r = client.get(f"/contracts/{contract_id}", headers=stranger_headers)
expect(r.status_code == 403, f"stranger should be forbidden: {r.status_code} {r.text}")
print("stranger forbidden from contract detail OK")

# 13. 납부 기록 (임대인이 납부 항목 생성 -> 둘 다 조회 가능)
r = client.post(
    f"/contracts/{contract_id}/payments",
    json={"type": "RENT", "due_date": "2026-02-01", "amount": 500000},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create payment failed: {r.status_code} {r.text}")
print("payment create OK")

r = client.get(f"/contracts/{contract_id}/payments", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"tenant payment list failed: {r.text}")
print("tenant 납부 기록 list OK")

# 13b. 임차인은 납부 항목을 생성할 수 없음
r = client.post(
    f"/contracts/{contract_id}/payments",
    json={"type": "RENT", "due_date": "2026-03-01", "amount": 500000},
    headers=tenant_headers,
)
expect(r.status_code == 403, f"tenant should not create payments: {r.status_code} {r.text}")
print("tenant forbidden from payment create OK")

# 14. 문제접수 기록 (실제 생성 API는 문제접수 담당 기능에서 구현 예정 -> 조회만 검증)
from app.database import SessionLocal  # noqa: E402
from app import models  # noqa: E402

db = SessionLocal()
db.add(
    models.IssueReport(
        contract_id=contract_id,
        category=models.IssueCategory.BOILER,
        description="보일러에서 물이 샙니다",
        status=models.IssueStatus.RECEIVED,
        responsible=models.Responsible.LANDLORD,
    )
)
db.commit()
db.close()

r = client.get(f"/contracts/{contract_id}/issues", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"issue list failed: {r.text}")
expect(r.json()[0]["category"] == "BOILER", f"issue category mismatch: {r.json()}")
print("문제접수 기록 list OK")

# 15. 비밀번호 변경
r = client.patch(
    "/auth/password",
    json={"current_password": "password123", "new_password": "newpassword456"},
    headers=landlord_headers,
)
expect(r.status_code == 204, f"password change failed: {r.status_code} {r.text}")
print("password change OK")

r = client.post("/auth/login", json={"phone": "01011112222", "password": "password123"})
expect(r.status_code == 401, f"old password should no longer work: {r.status_code} {r.text}")

r = client.post("/auth/login", json={"phone": "01011112222", "password": "newpassword456"})
expect(r.status_code == 200, f"new password should work: {r.status_code} {r.text}")
print("password change takes effect OK")

# 15b. 현재 비밀번호가 틀리면 거부
r = client.patch(
    "/auth/password",
    json={"current_password": "wrong-current", "new_password": "whatever1234"},
    headers=landlord_headers,
)
expect(r.status_code == 400, f"wrong current password should fail: {r.status_code} {r.text}")
print("wrong current password rejected OK")

# 16. 채팅알림설정 (기본값 -> 수정)
r = client.get("/users/me/notification-settings", headers=tenant_headers)
expect(r.status_code == 200 and r.json() == {
    "payment_alert": True,
    "issue_alert": True,
    "chat_alert": True,
}, f"default notification settings mismatch: {r.text}")
print("notification settings default OK")

r = client.put(
    "/users/me/notification-settings",
    json={"payment_alert": False, "issue_alert": True, "chat_alert": True},
    headers=tenant_headers,
)
expect(r.status_code == 200 and r.json()["payment_alert"] is False, f"notification settings update failed: {r.text}")
print("notification settings update OK")

r = client.get("/users/me/notification-settings", headers=tenant_headers)
expect(r.json()["payment_alert"] is False, f"notification settings not persisted: {r.text}")
print("notification settings persisted OK")

# --- 대시보드 기능 ---

# 17. 수리업체 등록 (임대인만)
r = client.post(
    f"/buildings/{building_id}/repair-vendors",
    json={"category": "BOILER", "name": "고려보일러", "phone": "021234567"},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create vendor failed: {r.status_code} {r.text}")
vendor_id = r.json()["id"]
print("repair vendor create OK")

r = client.post(
    f"/buildings/{building_id}/repair-vendors",
    json={"category": "BOILER", "name": "임차인이 등록 시도", "phone": "0000"},
    headers=tenant_headers,
)
expect(r.status_code == 403, f"tenant should not create vendor: {r.status_code} {r.text}")
print("tenant forbidden from vendor create OK")

# 18. 사전합의사항 등록 (임대인만 작성, 계약 당사자는 조회 가능)
r = client.post(
    f"/contracts/{contract_id}/agreements",
    json={"category": "BOILER", "responsible": "LANDLORD", "note": "노후 보일러는 임대인 부담"},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create agreement failed: {r.status_code} {r.text}")
agreement_id = r.json()["id"]
print("prior agreement create OK")

r = client.get(f"/contracts/{contract_id}/agreements", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"tenant agreement list failed: {r.text}")
print("tenant agreement read OK")

r = client.patch(
    f"/contracts/{contract_id}/agreements/{agreement_id}",
    json={"responsible": "TENANT", "note": "특약 수정"},
    headers=tenant_headers,
)
expect(r.status_code == 403, f"tenant should not edit agreement: {r.status_code} {r.text}")
print("tenant forbidden from agreement edit OK")

# 19. 수리업체 배정 (계약에 연결, 계약ID 기준)
r = client.patch(
    f"/contracts/{contract_id}/vendor",
    json={"vendor_id": vendor_id},
    headers=landlord_headers,
)
expect(r.status_code == 200 and r.json()["assigned_vendor"]["name"] == "고려보일러", f"assign vendor failed: {r.text}")
print("vendor assign OK")

# 20. 건물 대시보드 보드 (임대인 뷰): 세입자명/월세/납부상태/계약기간/수리업체 확인
r = client.get(f"/buildings/{building_id}/board", headers=landlord_headers)
expect(r.status_code == 200, f"landlord board failed: {r.status_code} {r.text}")
board = r.json()
expect(len(board) == 1, f"board should have exactly 1 row: {board}")
row = board[0]
expect(row["tenant_name"] == "세입자", f"board tenant_name mismatch: {row}")
expect(row["rent_amount"] == 500000, f"board rent mismatch: {row}")
expect(row["payment_status"] == "OVERDUE", f"board payment status should be OVERDUE (due 2026-02-01 already past): {row}")
expect(row["assigned_vendor"]["name"] == "고려보일러", f"board vendor mismatch: {row}")
print("landlord board OK (rent payment shows OVERDUE before confirm)")

# 20b. 임차인 뷰 (수정 불가 - PATCH 엔드포인트 자체가 require_landlord라 접근 자체가 막힘)
r = client.get("/users/me/board", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"tenant board failed: {r.text}")
print("tenant board (read-only) OK")

r = client.patch(f"/contracts/{contract_id}/vendor", json={"vendor_id": None}, headers=tenant_headers)
expect(r.status_code == 403, f"tenant should not reassign vendor: {r.status_code} {r.text}")
print("tenant forbidden from vendor reassignment OK")

# 21. 납부상태 확인 체크 (임대인이 입금 확인)
r = client.get(f"/contracts/{contract_id}/payments", headers=landlord_headers)
rent_payment_id = next(p["id"] for p in r.json() if p["type"] == "RENT")

r = client.patch(f"/payments/{rent_payment_id}/confirm", headers=landlord_headers)
expect(r.status_code == 200 and r.json()["status"] == "PAID", f"confirm payment failed: {r.text}")
print("payment confirm OK")

r = client.patch(f"/payments/{rent_payment_id}/confirm", headers=tenant_headers)
expect(r.status_code == 403, f"tenant should not confirm payment: {r.status_code} {r.text}")
print("tenant forbidden from payment confirm OK")

r = client.get(f"/buildings/{building_id}/board", headers=landlord_headers)
expect(r.json()[0]["payment_status"] == "PAID", f"board should reflect confirmed payment: {r.json()}")
print("board reflects confirmed payment OK")

# 22. D-3/D-day/연체 알림 대상 조회 (관리비 변동비를 정확히 D-3로 마감되게 추가)
d3_due = (date.today() + timedelta(days=3)).isoformat()
r = client.post(
    f"/contracts/{contract_id}/payments",
    json={"type": "MAINTENANCE_VARIABLE", "due_date": d3_due, "amount": 15000},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"create maintenance payment failed: {r.text}")

r = client.get("/notifications/due-payments", headers=landlord_headers)
expect(r.status_code == 200, f"due-payments alert failed: {r.status_code} {r.text}")
alerts = r.json()
expect(
    len(alerts) == 1 and alerts[0]["alert_type"] == "D-3" and alerts[0]["amount"] == 15000,
    f"expected exactly one D-3 alert for the maintenance payment: {alerts}",
)
print("due-payments D-3 alert detected OK")

# 22b. 임차인 쪽에서 조회해도 같은 계약이라 동일한 알림이 보여야 함
r = client.get("/notifications/due-payments", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"tenant due-payments alert failed: {r.text}")
print("tenant sees same due-payments alert OK")

# --- 채팅 기능 ---

# 23. 계약 생성 시 채팅방이 자동으로 생겼는지 (메시지는 아직 없음)
r = client.get(f"/contracts/{contract_id}/messages", headers=landlord_headers)
expect(r.status_code == 200, f"list messages failed: {r.status_code} {r.text}")
messages_before = r.json()
# 이미 21번 납부확인에서 시스템 메시지 1건이 쌓여 있어야 함
expect(
    len(messages_before) == 1 and messages_before[0]["type"] == "SYSTEM_PAYMENT",
    f"expected the payment-confirm system message already posted: {messages_before}",
)
print("chat room auto-created + payment-confirm system message present OK")

# 23b. 제3자는 메시지 접근 불가
r = client.get(f"/contracts/{contract_id}/messages", headers=stranger_headers)
expect(r.status_code == 403, f"stranger should not read messages: {r.status_code} {r.text}")
print("stranger forbidden from chat OK")

# 24. 일반 메시지 주고받기
r = client.post(f"/contracts/{contract_id}/messages", json={"content": "어제부터 찬바람이 안 나와요."}, headers=tenant_headers)
expect(r.status_code == 201 and r.json()["type"] == "TEXT" and r.json()["sender_name"] == "세입자", f"tenant send message failed: {r.text}")
print("tenant text message OK")

r = client.post(f"/contracts/{contract_id}/messages", json={"content": "확인했습니다. 업체에 연락해볼게요."}, headers=landlord_headers)
expect(r.status_code == 201 and r.json()["sender_name"] == "집주인", f"landlord send message failed: {r.text}")
print("landlord text message OK")

r = client.post(f"/contracts/{contract_id}/messages", json={"content": "몰래 보내기"}, headers=stranger_headers)
expect(r.status_code == 403, f"stranger should not send messages: {r.status_code} {r.text}")
print("stranger forbidden from sending message OK")

r = client.get(f"/contracts/{contract_id}/messages", headers=tenant_headers)
all_messages = r.json()
expect(len(all_messages) == 3, f"expected 3 messages total (1 system + 2 text): {all_messages}")
expect(all_messages[0]["type"] == "SYSTEM_PAYMENT" and all_messages[0]["sender_id"] is None, f"first message should be the system one: {all_messages}")
expect([m["type"] for m in all_messages[1:]] == ["TEXT", "TEXT"], f"order/type mismatch: {all_messages}")
print("message timeline (system + text, ordered) OK")

# 25. D-3 알림 실제 발송 (dispatch) + 멱등성 확인
r = client.post("/notifications/due-payments/dispatch", headers=landlord_headers)
expect(r.status_code == 200, f"dispatch failed: {r.status_code} {r.text}")
dispatched = r.json()
expect(len(dispatched) == 1 and dispatched[0]["alert_type"] == "D-3", f"expected exactly one D-3 dispatch: {dispatched}")
print("due-payment dispatch created system message OK")

r = client.get(f"/contracts/{contract_id}/messages", headers=landlord_headers)
after_dispatch = r.json()
expect(len(after_dispatch) == 4, f"expected 4 messages after dispatch: {after_dispatch}")
expect(after_dispatch[-1]["content"].startswith("[D-3]"), f"last message should be the D-3 alert: {after_dispatch[-1]}")
print("D-3 alert message visible in chat timeline OK")

# 25b. 같은 날 다시 dispatch 하면 중복 발송되지 않아야 함
r = client.post("/notifications/due-payments/dispatch", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 0, f"dispatch should be idempotent same-day: {r.text}")

r = client.get(f"/contracts/{contract_id}/messages", headers=landlord_headers)
expect(len(r.json()) == 4, f"message count should not grow on repeated dispatch: {r.json()}")
print("dispatch idempotency (no duplicate same-day alert) OK")

# --- FCM 디바이스 토큰 (Firebase 미설정 상태에서도 나머지 흐름이 안 깨지는지 확인) ---

# 26. 디바이스 토큰 등록 (임차인)
r = client.post(
    "/users/me/device-tokens",
    json={"token": "fcm-token-tenant-1", "platform": "android"},
    headers=tenant_headers,
)
expect(r.status_code == 201, f"register device token failed: {r.status_code} {r.text}")
print("device token register OK")

r = client.get("/users/me/device-tokens", headers=tenant_headers)
expect(r.status_code == 200 and len(r.json()) == 1, f"list device tokens failed: {r.text}")
print("device token list OK")

# 26b. 같은 토큰을 다른 사용자가 등록하면 소유자가 갱신됨(기기 재로그인 시나리오)
r = client.post(
    "/users/me/device-tokens",
    json={"token": "fcm-token-tenant-1", "platform": "android"},
    headers=landlord_headers,
)
expect(r.status_code == 201, f"re-register device token failed: {r.text}")

r = client.get("/users/me/device-tokens", headers=tenant_headers)
expect(len(r.json()) == 0, f"token should have moved to the new owner: {r.json()}")
r = client.get("/users/me/device-tokens", headers=landlord_headers)
expect(len(r.json()) == 1, f"landlord should now own the token: {r.json()}")
print("device token re-registration (ownership transfer) OK")

# 27. 토큰이 등록된 상태로 메시지를 보내도(Firebase 미설정) 죽지 않고 정상 처리되는지
r = client.post(f"/contracts/{contract_id}/messages", json={"content": "푸시 테스트 메시지"}, headers=tenant_headers)
expect(r.status_code == 201, f"send message with registered token failed: {r.status_code} {r.text}")
print("send message with device token registered (FCM unset, no crash) OK")

# 28. 디바이스 토큰 해제
r = client.delete("/users/me/device-tokens/fcm-token-tenant-1", headers=landlord_headers)
expect(r.status_code == 204, f"unregister device token failed: {r.status_code} {r.text}")

r = client.delete("/users/me/device-tokens/no-such-token", headers=landlord_headers)
expect(r.status_code == 404, f"unregistering nonexistent token should 404: {r.status_code} {r.text}")
print("device token unregister OK")

print("\nALL SMOKE TESTS PASSED")
