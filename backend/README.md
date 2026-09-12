# Backend (로그인 · 프로필 · 대시보드 · 채팅 · FCM · 문제접수)

FastAPI + SQLite. 임대인/임차인 로그인, 건물/호실/계약, 초대코드, 프로필(지난 계약·비번수정·알림설정), 대시보드(건물별 보드·사전합의사항·수리업체·납부알림), 채팅(계약별 1:1 채팅방 + 시스템 메시지), FCM 푸시(디바이스 토큰 등록 + 채팅 이벤트 발송), 문제접수(사진 업로드·사전합의 자동매칭·해결처리) 흐름을 구현.

## 실행 방법

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate / macOS·Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # JWT_SECRET_KEY를 랜덤 값으로 채워야 함 (필수 — 없으면 서버가 시작되지 않음)
uvicorn app.main:app --reload
```

`JWT_SECRET_KEY` 랜덤 값 생성: `python -c "import secrets; print(secrets.token_hex(32))"`

`http://127.0.0.1:8000/docs` 에서 Swagger UI로 바로 테스트 가능.

## 플로우

1. 임대인 가입: `POST /auth/signup/landlord`
2. 건물 등록: `POST /buildings`
3. 호실 등록: `POST /buildings/{building_id}/units`
4. 계약 등록: `POST /units/{unit_id}/contracts`
5. 초대코드 발급: `POST /units/{unit_id}/contracts/{contract_id}/invite-code`
6. 임차인 가입: `POST /auth/signup/tenant` (초대코드 없이 일반 가입 — 이름/전화번호/비밀번호만)
7. 로그인: `POST /auth/login` → JWT 발급
8. 초대코드로 계약 연결: `POST /auth/redeem-invite-code` (로그인 상태, body: `{invite_code}`) — **가입과 완전히 분리된 단계**. 같은 임차인 계정으로 여러 번 호출해서 계약을 순차적으로 여러 개 연결할 수 있음(재계약, 이사 등) — `GET /users/me/contracts`("지난 계약")가 바로 이 계정에 연결된 계약들
9. 내 정보 조회: `GET /auth/me` (Authorization: Bearer {token})

### 프로필

- 비번 수정: `PATCH /auth/password` (현재/새 비밀번호)
- 지난 계약 목록: `GET /users/me/contracts` — 임대인은 본인이 등록한 계약, 임차인은 본인이 연결된 계약만 요약(건물명+호실+기간) 리턴
- 계약 상세: `GET /contracts/{contract_id}` — 해당 계약의 임대인/임차인만 조회 가능(제3자 403)
- 납부 기록: `GET /contracts/{contract_id}/payments`, 생성은 `POST /contracts/{contract_id}/payments` (임대인만)
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

### 채팅

계약당 채팅방 1개(호실이 아니라 **계약ID 기준** — 계약 생성 시 자동으로 만들어짐, `POST /units/{unit_id}/contracts` 호출 시점).

- 메시지 목록: `GET /contracts/{contract_id}/messages` — 계약 당사자만, 일반 메시지/시스템 메시지가 한 타임라인에 시간순으로 섞여서 나옴 (`type`이 `TEXT`면 일반, `SYSTEM_ISSUE`/`SYSTEM_PAYMENT`면 시스템 — 프론트에서 이 값으로 말풍선/카드 UI를 구분)
- 메시지 전송: `POST /contracts/{contract_id}/messages` (body: `content`) — 계약 당사자만, 항상 `TEXT` 타입
- 시스템 메시지는 사용자가 직접 못 만들고, 백엔드 이벤트가 자동으로 남김:
  - 납부확인(`PATCH /payments/{id}/confirm`) 처리 시 "OO월 OO가 납부 완료 처리되었습니다" 자동 게시
  - `POST /notifications/due-payments/dispatch` — 시스템 전체의 D-3/D-day/연체 대상을 훑어서 각 계약 채팅방에 "OO월 OO 납부일이 3일 남았습니다" 류 메시지를 실제로 남김. 같은 결제건+알림종류는 하루에 한 번만 남기도록 멱등 처리(당일 채팅 메시지 존재 여부로 체크)
  - **문제접수 기능에서 재사용할 것**: [app/chat_service.py](app/chat_service.py)의 `post_system_message(db, contract_id, ChatMessageType.SYSTEM_ISSUE, "...", ref_id=issue.id)`를 그대로 import해서 호출하면 됨(같은 프로세스라 HTTP 안 거치고 바로 함수 호출). 신고 접수/상태 변경 시 이걸 불러서 "에어컨 문제가 접수되었습니다", "처리 상태가 'OOO'으로 변경되었습니다" 같은 메시지를 남기면 된다. `SYSTEM_ISSUE` 타입 메시지의 `ref_id`는 `issue_reports.id`를 가리키므로, 프론트는 그 id로 `GET /contracts/{id}/issues`에서 상세를 가져와 "문제 카드"로 렌더링.

**한계**: `dispatch` 엔드포인트는 원래 하루 한 번 도는 스케줄러(cron)가 호출해야 하는데, 그 스케줄러 자체는 이 세션에서 만들지 않았다. 지금은 로그인한 사용자 누구나 호출 가능한 임시 상태이고, 실제 배포 시엔 사용자 토큰이 아니라 전용 서비스 자격 증명으로 바꿔야 한다. (실제 폰 푸시 발송 자체는 아래 FCM 섹션에서 구현됨.)

### FCM 푸시

- 디바이스 토큰 등록: `POST /users/me/device-tokens` (body: `{token, platform?}`) — 앱이 로그인 직후 또는 토큰 갱신 시 호출. 같은 토큰이 이미 등록돼 있으면 소유자를 현재 로그인 사용자로 갱신(기기 재설치/다른 계정 로그인 대응)
- 내 디바이스 토큰 목록: `GET /users/me/device-tokens`
- 디바이스 토큰 해제: `DELETE /users/me/device-tokens/{token}` — 로그아웃 시 호출
- 발송 트리거 지점(전부 [app/chat_service.py](app/chat_service.py) 경유):
  - 시스템 메시지가 남을 때(`post_system_message`) → 그 계약의 임대인+임차인 양쪽에게 푸시
  - 일반 텍스트 메시지를 보낼 때(`post_text_message`) → 보낸 사람 제외한 상대방에게 푸시
  - 발송 전 `notification_settings`(`payment_alert`/`issue_alert`/`chat_alert`)를 확인해서 꺼져있으면 그 사람에겐 안 보냄
- 실제 발송은 [app/push_service.py](app/push_service.py)가 담당. **`FIREBASE_CREDENTIALS_PATH` 환경변수가 없으면 실제 발송 없이 로그만 남기고 조용히 스킵** — Firebase 프로젝트 없이도 로컬 개발/스모크 테스트가 깨지지 않게 하려는 설계. 실제 배포 시 Firebase 콘솔 > 프로젝트 설정 > 서비스 계정에서 발급받은 JSON 파일 경로를 `.env`에 설정하면 그때부터 실제로 나감.

**Firebase 설정 방법**:
1. Firebase 콘솔 → 이 프로젝트 선택 → 프로젝트 설정 → 서비스 계정 탭 → "새 비공개 키 생성"
2. 다운로드된 JSON 파일을 `backend/` 폴더 안에 저장 (파일명 아무거나 상관없음 — `.gitignore`에 `*firebase-adminsdk*.json` 패턴으로 이미 제외돼 있어서 git에 절대 안 올라감)
3. `backend/.env.example`을 복사해서 `backend/.env` 만들고, `FIREBASE_CREDENTIALS_PATH`에 그 JSON 파일 경로 입력(예: `./firebase-adminsdk-xxxxx.json`)
4. `.env`는 `python-dotenv`로 앱 시작 시 자동 로드됨([app/\_\_init\_\_.py](app/__init__.py)) — 서버 재시작만 하면 적용됨

주의: 이 JSON 키 파일은 **비밀키**라서 Slack/카톡 등으로 공유하지 말고, 팀원 각자 위 절차대로 Firebase 콘솔에서 직접 발급받는 걸 추천. (같은 서비스 계정 키를 여러 명이 공유해야 하는 상황이면, 안전한 채널로만 전달하고 공개 저장소에는 절대 올리지 말 것.)

### 문제접수

전부 계약ID 기준(`/contracts/{contract_id}/issues...`).

- 접수: `POST /contracts/{contract_id}/issues` (body: `category`, `description`, `photo_url?`) — 계약 당사자만. 같은 카테고리의 `prior_agreements`가 있으면 그 `responsible`를 그대로 적용하고 상태를 `RECEIVED`로, 없으면 `responsible=UNDEFINED`/상태 `IN_CHAT`으로 접수해서 채팅으로 넘김. 응답에 `agreement_matched`(사전합의 매칭 여부)와 `next_action`(`FOLLOW_AGREEMENT`/`OPEN_CHAT`) 포함
- 목록/단건 조회: `GET /contracts/{contract_id}/issues`, `GET /contracts/{contract_id}/issues/{issue_id}` — 계약 당사자만
- 상태 변경: `PATCH /contracts/{contract_id}/issues/{issue_id}/status` — 임대인만
- 해결 처리: `POST /contracts/{contract_id}/issues/{issue_id}/resolve` (body: `resolver`, `resolved_detail`, `cost`, `payer`, `payment_status`, `receipt_image_url?`) — 상태를 `RESOLVED`로 변경
- 사진 업로드: `POST /uploads/issues`, `POST /uploads/receipts` (multipart `file`) — jpg/png/webp/gif만, 최대 10MB. 반환된 `url`(`/uploads/issues/{파일명}`)을 그대로 `photo_url`/`receipt_image_url`에 넣으면 됨. 업로드된 파일은 `/uploads/...`로 정적 서빙됨
- 접수/상태변경/해결 시점마다 `chat_service.post_system_message()`를 그대로 재사용해서 `SYSTEM_ISSUE` 채팅 메시지가 자동으로 남음(신고 접수 시 어떤 처리 방향인지, 상태 변경, 해결 비용/부담주체까지)

## 스키마

`users` / `buildings` / `units` / `contracts` / `invite_codes` / `payments` / `issue_reports` / `notification_settings` / `repair_vendors` / `prior_agreements` / `chat_rooms` / `chat_messages` / `device_tokens` 13개 테이블. 관계는 루트 [README.md](../README.md)의 데이터 인터페이스 문서 및 대화 내 스키마 설계 참고.

- `units`는 물리적 호실(건물+동+호 유일), `contracts`가 계약(기간+임대인+임차인) 단위 — 같은 호실도 계약이 바뀌면 새 `contracts` row가 생성되어 이전 임차인 데이터와 분리됨.
- 초대코드는 계약 1건당 발급, 1회용(`used_at`), 7일 만료(`expires_at`).
- `buildings.name`은 선택 입력 — "고려빌라"처럼 목록/카드에 보여줄 짧은 이름이고, 없으면 `address`로 대체 표시.
- `issue_reports`의 `category`/`responsible` 코드값은 [루트 README](../README.md)에서 문제접수 담당자와 합의한 값과 동일(`BOILER`/`WATER`/`ELECTRIC`/`WALL`/`FURNITURE`/`ETC`, `LANDLORD`/`TENANT`/`UNDEFINED`). `repair_vendors.category`와 `prior_agreements.category`/`responsible`도 동일 코드값 재사용.
- `payments.status`는 DB에 저장된 값과 별개로, 조회 시점에 `due_date`를 오늘과 비교해서 PENDING→OVERDUE로 즉시 계산한 값을 보여줌([app/utils.py](app/utils.py)의 `effective_payment_status`). 별도 배치/크론 없이도 항상 최신 상태.
- `contracts.assigned_vendor_id`가 "선택옵션(수리업체 번호)"에 해당 — 호실이 아니라 계약에 매달려 있어서 임차인이 바뀌면 자동으로 초기화됨.
- `issue_reports`는 팀원의 해결처리 기능으로 컬럼이 늘어남: `resolver`(누가 해결했는지: `LANDLORD`/`TENANT`/`REPAIR_VENDOR`), `cost`, `payer`(`LANDLORD`/`TENANT`/`SHARED`), `payment_status`(`PENDING`/`PAID`), `receipt_image_url`. 테이블 개수 자체는 그대로(13개), 기존 컬럼 확장만 있음.

## 스모크 테스트

```bash
python smoke_test.py
```

가입→건물/호실/계약 생성→초대코드→임차인가입(초대코드 분리)→로그인→초대코드 redeem(같은 계정으로 두 번째 계약까지), 프로필(지난 계약 조회, 계약 상세, 납부 기록, 비번 수정, 알림설정), 대시보드(수리업체 등록, 사전합의사항, 계약별 수리업체 배정, 건물/내 보드 조회, 납부확인 체크, D-3 알림 감지), 채팅(채팅방 자동생성, 납부확인 시 시스템 메시지 자동 게시, 일반 메시지 송수신, D-3 알림 실제 발송과 멱등성), FCM(디바이스 토큰 등록/소유권 이전/해제, Firebase 미설정 상태에서 메시지 발송이 죽지 않는지), 문제접수(사전합의 매칭/미매칭 분기, 상태변경, 해결처리, 시스템 메시지 자동게시)까지 전체 플로우와 주요 실패 케이스(중복 호실, 재사용 초대코드, 오답 비밀번호, 권한 없는 접근, 제3자 계약/채팅/문제접수 접근 차단, 임차인의 쓰기 권한 없는 엔드포인트 접근 차단)를 한번에 검증.
