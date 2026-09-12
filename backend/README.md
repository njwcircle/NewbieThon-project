# Backend (로그인 · 프로필 · 대시보드)

FastAPI + SQLite. 임대인/임차인 로그인, 건물/호실/계약, 초대코드, 프로필(지난 계약·비번수정·알림설정), 대시보드(건물별 보드·사전합의사항·수리업체·납부알림) 흐름을 구현.

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

### 대시보드

모든 조회/조작은 **호실ID가 아니라 계약ID 기준**(같은 호실도 임차인이 바뀌면 계약이 바뀌므로).

- 건물 리스트: `GET /buildings` (이미 로그인 단계에서 구현)
- 수리업체 등록/조회/수정/삭제: `POST|GET /buildings/{building_id}/repair-vendors`, `PATCH|DELETE /repair-vendors/{vendor_id}` — 전부 임대인 전용
- 사전합의사항 등록/조회/수정/삭제: `POST|GET /contracts/{contract_id}/agreements`, `PATCH|DELETE /contracts/{contract_id}/agreements/{agreement_id}` — 작성/수정/삭제는 임대인만, 조회는 계약 당사자(임대인·임차인) 모두 가능
- 건물 보드(임대인 뷰): `GET /buildings/{building_id}/board` — 건물의 모든 호실을 순회하며 각 호실의 현재 활성 계약 기준으로 세입자명·월세·관리비(고정비)·계약기간·납부상태·배정된 수리업체를 한 번에 반환. 계약이 없는 호실(공실)은 호실 정보만 채워짐
- 내 계약 보드(임차인 뷰): `GET /users/me/board` — 본인이 연결된 활성 계약만 같은 형태로 반환(수정 엔드포인트가 전부 임대인 전용이라 자연히 읽기 전용)
- 수리업체 배정: `PATCH /contracts/{contract_id}/vendor` (body: `vendor_id` 또는 `null`) — 임대인만
- 납부상태 확인 체크: `PATCH /payments/{payment_id}/confirm` — 임대인이 입금 확인 후 수동으로 PAID 처리
- D-3/D-day/연체 알림 대상 조회: `GET /notifications/due-payments` — 로그인한 사용자(임대인/임차인) 본인 관련 계약의 미납 건 중 `due_date`가 오늘+3일/오늘/오늘 이전인 것만 반환

## 스키마

`users` / `buildings` / `units` / `contracts` / `invite_codes` / `payments` / `issue_reports` / `notification_settings` / `repair_vendors` / `prior_agreements` 10개 테이블. 관계는 루트 [README.md](../README.md)의 데이터 인터페이스 문서 및 대화 내 스키마 설계 참고.

- `units`는 물리적 호실(건물+동+호 유일), `contracts`가 계약(기간+임대인+임차인) 단위 — 같은 호실도 계약이 바뀌면 새 `contracts` row가 생성되어 이전 임차인 데이터와 분리됨.
- 초대코드는 계약 1건당 발급, 1회용(`used_at`), 7일 만료(`expires_at`).
- `buildings.name`은 선택 입력 — "고려빌라"처럼 목록/카드에 보여줄 짧은 이름이고, 없으면 `address`로 대체 표시.
- `issue_reports`의 `category`/`responsible` 코드값은 [루트 README](../README.md)에서 문제접수 담당자와 합의한 값과 동일(`BOILER`/`WATER`/`ELECTRIC`/`WALL`/`FURNITURE`/`ETC`, `LANDLORD`/`TENANT`/`UNDEFINED`). `repair_vendors.category`와 `prior_agreements.category`/`responsible`도 동일 코드값 재사용.
- `payments.status`는 DB에 저장된 값과 별개로, 조회 시점에 `due_date`를 오늘과 비교해서 PENDING→OVERDUE로 즉시 계산한 값을 보여줌([app/utils.py](app/utils.py)의 `effective_payment_status`). 별도 배치/크론 없이도 항상 최신 상태.
- `contracts.assigned_vendor_id`가 "선택옵션(수리업체 번호)"에 해당 — 호실이 아니라 계약에 매달려 있어서 임차인이 바뀌면 자동으로 초기화됨.

### 알림(D-3/D-day/연체) 관련 한계

`GET /notifications/due-payments`는 **알림 대상 목록만 계산**해서 돌려줍니다. 실제로 사용자 휴대폰에 푸시를 보내거나 카카오 알림톡을 발송하는 부분은 이 세션에서 만들지 않았어요 — FCM/카카오 비즈니스 채널 같은 외부 발송 채널 연동과 그걸 주기적으로 실행할 스케줄러(cron)가 별도로 필요합니다. 이 엔드포인트를 그 스케줄러가 주기적으로 폴링해서, 결과를 채팅 시스템 메시지나 실제 푸시로 내보내는 다음 단계 작업이 남아있습니다.

## 스모크 테스트

```bash
python smoke_test.py
```

가입→건물/호실/계약 생성→초대코드→임차인가입→로그인, 프로필(지난 계약 조회, 계약 상세, 납부 기록, 문제접수 기록 조회, 비번 수정, 알림설정), 대시보드(수리업체 등록, 사전합의사항, 계약별 수리업체 배정, 건물/내 보드 조회, 납부확인 체크, D-3 알림 감지)까지 전체 플로우와 주요 실패 케이스(중복 호실, 재사용 초대코드, 오답 비밀번호, 권한 없는 접근, 제3자 계약 조회 차단, 임차인의 쓰기 권한 없는 엔드포인트 접근 차단)를 한번에 검증.
