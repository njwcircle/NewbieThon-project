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
r = client.post("/buildings", json={"address": "서울시 어딘가 101동"}, headers=landlord_headers)
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

print("\nALL SMOKE TESTS PASSED")
