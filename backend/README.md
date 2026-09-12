# Backend (로그인 · 프로필)

FastAPI + SQLite. 임대인/임차인 로그인, 건물/호실/계약, 초대코드, 프로필(지난 계약·비번수정·알림설정) 흐름을 구현.

## 실행 방법

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate / macOS·Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs` 에서 Swagger UI로 바로 테스트 가능.

## 플로우

1. 임대인 가입: `POST /auth/signup/landlord`
2. 건물 등록: `POST /buildings`
3. 호실 등록: `POST /buildings/{building_id}/units`
4. 계약 등록: `POST /units/{unit_id}/contracts`
5. 초대코드 발급: `POST /units/{unit_id}/contracts/{contract_id}/invite-code`
6. 임차인 가입(초대코드 사용): `POST /auth/signup/tenant`
7. 로그인: `POST /auth/login` → JWT 발급
8. 내 정보 조회: `GET /auth/me` (Authorization: Bearer {token})

### 프로필

- 비번 수정: `PATCH /auth/password` (현재/새 비밀번호)
- 지난 계약 목록: `GET /users/me/contracts` — 임대인은 본인이 등록한 계약, 임차인은 본인이 연결된 계약만 요약(건물명+호실+기간) 리턴
- 계약 상세: `GET /contracts/{contract_id}` — 해당 계약의 임대인/임차인만 조회 가능(제3자 403)
- 납부 기록: `GET /contracts/{contract_id}/payments`, 생성은 `POST /contracts/{contract_id}/payments` (임대인만)
- 문제접수 기록: `GET /contracts/{contract_id}/issues` — **읽기 전용.** 생성(신고 접수) API는 문제접수 담당 기능에서 `issue_reports` 테이블에 직접 쓰는 방식으로 붙을 예정이라 아직 없음.
- 채팅알림설정: `GET/PUT /users/me/notification-settings` — `payment_alert`/`issue_alert`/`chat_alert` 개별 on/off, 기본값 전부 true

## 스키마

`users` / `buildings` / `units` / `contracts` / `invite_codes` / `payments` / `issue_reports` / `notification_settings` 8개 테이블. 관계는 루트 [README.md](../README.md)의 데이터 인터페이스 문서 및 대화 내 스키마 설계 참고.

- `units`는 물리적 호실(건물+동+호 유일), `contracts`가 계약(기간+임대인+임차인) 단위 — 같은 호실도 계약이 바뀌면 새 `contracts` row가 생성되어 이전 임차인 데이터와 분리됨.
- 초대코드는 계약 1건당 발급, 1회용(`used_at`), 7일 만료(`expires_at`).
- `buildings.name`은 선택 입력 — "고려빌라"처럼 목록/카드에 보여줄 짧은 이름이고, 없으면 `address`로 대체 표시.
- `issue_reports`의 `category`/`responsible` 코드값은 [루트 README](../README.md)에서 문제접수 담당자와 합의한 값과 동일(`BOILER`/`WATER`/`ELECTRIC`/`WALL`/`FURNITURE`/`ETC`, `LANDLORD`/`TENANT`/`UNDEFINED`).

## 스모크 테스트

```bash
python smoke_test.py
```

가입→건물/호실/계약 생성→초대코드→임차인가입→로그인, 그리고 프로필(지난 계약 조회, 계약 상세, 납부 기록, 문제접수 기록 조회, 비번 수정, 알림설정)까지 전체 플로우와 주요 실패 케이스(중복 호실, 재사용 초대코드, 오답 비밀번호, 권한 없는 접근, 제3자 계약 조회 차단)를 한번에 검증.
