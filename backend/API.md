# API 레퍼런스 (프론트엔드 연동용)

베이스 URL: `http://127.0.0.1:8000` (로컬 개발). `http://127.0.0.1:8000/docs`에서 Swagger로 직접 호출 테스트 가능.

## 공통 규칙

- **인증**: 로그인/가입 API를 제외한 모든 요청에 `Authorization: Bearer {access_token}` 헤더 필요.
- **에러 응답**: 전부 `{"detail": "에러 메시지"}` 형태 (상태코드 400/401/403/404).
- **날짜**: `YYYY-MM-DD` (예: `"2026-03-01"`)
- **ID 기준**: 호실(unit)이 아니라 **계약(contract) 기준**으로 대부분의 리소스가 스코핑됨 — 같은 호실이라도 임차인이 바뀌면 계약이 새로 생기고 이전 데이터와 분리됨.

## Enum 코드값

| Enum | 값 |
|---|---|
| `role` | `LANDLORD`, `TENANT` |
| `contract.status` | `ACTIVE`, `ENDED` |
| `payment.type` | `RENT`, `MAINTENANCE_FIXED`, `MAINTENANCE_VARIABLE` |
| `payment.status` | `PENDING`, `PAID`, `OVERDUE` (조회 시점에 자동 계산됨, DB 저장값과 다를 수 있음) |
| `issue.category` / `repair_vendor.category` | `BOILER`, `WATER`, `ELECTRIC`, `WALL`, `FURNITURE`, `ETC` |
| `responsible` (issue/agreement) | `LANDLORD`, `TENANT`, `UNDEFINED` |
| `issue.status` | `RECEIVED`, `AUTO_RESOLVED`, `IN_CHAT`, `RESOLVED` |
| `chat_message.type` | `TEXT`, `SYSTEM_ISSUE`, `SYSTEM_PAYMENT` |
| `alert_type` (due-payments) | `"D-3"`, `"D-DAY"`, `"OVERDUE"` |

---

## 1. 로그인 / 인증

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| POST | `/auth/signup/landlord` | 없음 | `{name, phone, password}` | `{access_token, token_type, role}` |
| POST | `/auth/signup/tenant` | 없음 | `{invite_code, name, phone, password}` | `{access_token, token_type, role}` |
| POST | `/auth/login` | 없음 | `{phone, password}` | `{access_token, token_type, role}` |
| GET | `/auth/me` | 로그인 | - | `{id, role, name, phone}` |
| PATCH | `/auth/password` | 로그인 | `{current_password, new_password}` | 204 |

## 2. 건물 / 호실 / 계약 / 초대코드

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| POST | `/buildings` | 임대인 | `{name?, address}` | `{id, name, address}` |
| GET | `/buildings` | 임대인 | - | `[{id, name, address}]` (본인 건물만) |
| POST | `/buildings/{building_id}/units` | 임대인 | `{dong, ho}` | `{id, building_id, dong, ho}` |
| GET | `/buildings/{building_id}/units` | 임대인 | - | `[...]` |
| POST | `/units/{unit_id}/contracts` | 임대인 | `{rent_amount, maintenance_fee_fixed, start_date, end_date}` | `{id, unit_id, rent_amount, maintenance_fee_fixed, start_date, end_date, status, tenant_id}` |
| GET | `/units/{unit_id}/contracts` | 임대인 | - | `[...]` |
| POST | `/units/{unit_id}/contracts/{contract_id}/invite-code` | 임대인 | - | `{code, contract_id, expires_at}` (7일 만료, 1회용) |

## 3. 프로필

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| GET | `/users/me/contracts` | 로그인 | - | `[{id, building_name, dong, ho, start_date, end_date, status}]` — "지난 계약" 카드 목록 |
| GET | `/contracts/{contract_id}` | 계약 당사자 | - | `{id, building_name, address, dong, ho, rent_amount, maintenance_fee_fixed, start_date, end_date, status}` |
| GET | `/contracts/{contract_id}/payments` | 계약 당사자 | - | `[{id, type, due_date, amount, status, paid_at}]` |
| POST | `/contracts/{contract_id}/payments` | 임대인 | `{type, due_date, amount}` | `{id, type, due_date, amount, status, paid_at}` |
| GET | `/users/me/notification-settings` | 로그인 | - | `{payment_alert, issue_alert, chat_alert}` |
| PUT | `/users/me/notification-settings` | 로그인 | `{payment_alert, issue_alert, chat_alert}` | 위와 동일 |

## 4. 대시보드

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| POST | `/buildings/{building_id}/repair-vendors` | 임대인 | `{category, name, phone}` | `{id, building_id, category, name, phone}` |
| GET | `/buildings/{building_id}/repair-vendors` | 임대인 | - | `[...]` |
| PATCH | `/repair-vendors/{vendor_id}` | 임대인 | `{category, name, phone}` | `{...}` |
| DELETE | `/repair-vendors/{vendor_id}` | 임대인 | - | 204 |
| POST | `/contracts/{contract_id}/agreements` | 임대인 | `{category, responsible, note?}` | `{id, contract_id, category, responsible, note}` |
| GET | `/contracts/{contract_id}/agreements` | 계약 당사자 | - | `[...]` |
| PATCH | `/contracts/{contract_id}/agreements/{agreement_id}` | 임대인 | `{responsible, note?}` | `{...}` |
| DELETE | `/contracts/{contract_id}/agreements/{agreement_id}` | 임대인 | - | 204 |
| GET | `/buildings/{building_id}/board` | 임대인 | - | `[BoardRow]` — 건물의 모든 호실, 아래 표 참고 |
| GET | `/users/me/board` | 로그인(임차인 관점) | - | `[BoardRow]` — 본인 계약만 |
| PATCH | `/contracts/{contract_id}/vendor` | 임대인 | `{vendor_id: string \| null}` | `BoardRow` |
| PATCH | `/payments/{payment_id}/confirm` | 임대인 | - | `{id, type, due_date, amount, status: "PAID", paid_at}` |
| GET | `/notifications/due-payments` | 로그인 | - | `[DuePaymentAlert]` — 본인 관련 계약의 D-3/D-day/연체 미리보기 |
| POST | `/notifications/due-payments/dispatch` | 로그인 | - | `[DuePaymentAlert]` — 전체 시스템 훑어서 실제로 채팅에 메시지 남김 (스케줄러용, 임시로 아무 로그인 사용자나 호출 가능) |

**BoardRow**: `{unit_id, dong, ho, contract_id, tenant_name, rent_amount, maintenance_fee_fixed, start_date, end_date, payment_status, assigned_vendor: {id, building_id, category, name, phone} | null}` — 계약 없는 공실은 `unit_id/dong/ho`만 채워지고 나머지는 `null`.

**DuePaymentAlert**: `{payment_id, contract_id, building_name, dong, ho, due_date, amount, type, alert_type}`

## 5. 채팅

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| GET | `/contracts/{contract_id}/messages` | 계약 당사자 | - | `[{id, type, sender_id, sender_name, content, ref_id, created_at}]` (시간순, 일반+시스템 메시지 섞여있음) |
| POST | `/contracts/{contract_id}/messages` | 계약 당사자 | `{content}` | 위와 동일 (항상 `type: "TEXT"`) |

- `sender_id`가 `null`이면 시스템 메시지 → 프론트에서 말풍선 대신 카드/배너 UI로 렌더링
- `type: "SYSTEM_ISSUE"`인 메시지는 `ref_id`가 `issue_reports.id`를 가리킴 → 그 id로 `GET /contracts/{contract_id}/issues` 결과에서 찾아서 "문제 카드"로 표시
- 날짜 구분선("──── 9월 12일 ────")은 `created_at` 날짜가 바뀔 때 프론트에서 그리면 됨(백엔드는 타임스탬프만 줌)

## 6. FCM 푸시

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| POST | `/users/me/device-tokens` | 로그인 | `{token, platform?}` | `{id, token, platform}` — 앱 로그인 직후/토큰 갱신 시 호출 |
| GET | `/users/me/device-tokens` | 로그인 | - | `[{id, token, platform}]` |
| DELETE | `/users/me/device-tokens/{token}` | 로그인 | - | 204 — 로그아웃 시 호출 |

- 채팅 메시지(일반/시스템)가 발생할 때마다 상대방에게 자동으로 푸시가 나가요. 프론트는 토큰 등록/해제만 신경 쓰면 되고, "언제 보낼지"는 백엔드가 알아서 처리.
- 각 사용자의 `notification_settings`(`payment_alert`/`issue_alert`/`chat_alert`)가 꺼져있으면 그 사람에겐 안 감.
- 로컬 개발 중엔 Firebase 프로젝트가 없어도 에러 없이 그냥 스킵되니, 프론트 개발 중엔 폰에 실제로 알림이 안 와도 정상입니다 (서버 로그에 `[FCM skip] ...`만 찍힘).

## 7. 문제접수

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| POST | `/contracts/{contract_id}/issues` | 계약 당사자 | `{category, description, photo_url?}` | `{issue: IssueReportResponse, agreement_matched, agreement_note, next_action}` |
| GET | `/contracts/{contract_id}/issues` | 계약 당사자 | - | `[IssueReportResponse]` |
| GET | `/contracts/{contract_id}/issues/{issue_id}` | 계약 당사자 | - | `IssueReportResponse` |
| PATCH | `/contracts/{contract_id}/issues/{issue_id}/status` | 임대인 | `{status}` | `IssueReportResponse` |
| POST | `/contracts/{contract_id}/issues/{issue_id}/resolve` | 계약 당사자 | `{resolver, resolved_detail, cost, payer, payment_status, receipt_image_url?}` | `IssueReportResponse` (`status`가 `RESOLVED`로 바뀜) |
| POST | `/uploads/issues` | 없음 | multipart `file` | `{url}` — jpg/png/webp/gif, 최대 10MB |
| POST | `/uploads/receipts` | 없음 | multipart `file` | `{url}` |

**IssueReportResponse**: `{id, contract_id, category, description, photo_url, status, responsible, resolver, resolved_detail, cost, payer, payment_status, receipt_image_url, created_at, resolved_at}`

- 접수 시 같은 카테고리의 사전합의사항이 있으면 자동으로 그 `responsible`을 적용(`agreement_matched: true`, `next_action: "FOLLOW_AGREEMENT"`), 없으면 `responsible: "UNDEFINED"`/`status: "IN_CHAT"`으로 접수되고 채팅으로 넘어감(`next_action: "OPEN_CHAT"`)
- 업로드는 인증 없이 호출 가능 — 반환된 `url`을 그대로 `photo_url`/`receipt_image_url`에 넣으면 됨. 실제 이미지는 `<base>{url}`로 바로 접근 가능(정적 서빙)
- 접수/상태변경/해결마다 해당 계약 채팅방에 `SYSTEM_ISSUE` 시스템 메시지가 자동으로 남음 — 4번(채팅) 섹션과 동일하게 `ref_id`가 `issue_reports.id`를 가리킴

## 8. 법률에이전트

| Method | Path | 권한 | Body | 응답 |
|---|---|---|---|---|
| POST | `/contracts/{contract_id}/legal-advice` | 계약 당사자 | `{category, custom_category?, question}` | `{category, answer, contract_id, referenced_issue_ids, referenced_agreement_ids, disclaimer}` |

- `category`: `RENT`/`DEPOSIT`/`REPAIR_COST`/`CONTRACT`/`DEFECT`/`EVICTION`/`ETC`
- 백엔드가 해당 계약의 사전합의사항 + 최근 문제접수 기록을 모아서 LLM(기본 Google Gemini, 환경변수로 교체 가능)에 같이 전달 → 답변이 실제 계약 데이터를 참고함
- **`LEGAL_LLM_API_KEY`/`LEGAL_LLM_MODEL`이 서버에 설정 안 돼 있으면 503** — 프론트는 이 경우 "법률 상담 기능 준비 중"처럼 안내하고 나머지 화면은 그대로 쓰면 됨
- `answer`는 항상 disclaimer 포함, 법적 결론을 단정하지 않고 "확인이 필요하다" 식으로 안내하도록 프롬프트가 설계돼 있음
