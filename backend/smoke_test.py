"""One-off smoke test for the login/building/unit/contract flow. Not a permanent test file."""

import os

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

print("\nALL SMOKE TESTS PASSED")
