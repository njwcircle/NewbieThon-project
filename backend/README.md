# Backend (로그인 기능)

FastAPI + SQLite. 임대인/임차인 로그인, 건물/호실/계약, 초대코드 흐름을 구현.

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

## 스키마

`users` / `buildings` / `units` / `contracts` / `invite_codes` 5개 테이블. 관계는 루트 [README.md](../README.md)의 데이터 인터페이스 문서 및 대화 내 스키마 설계 참고.

- `units`는 물리적 호실(건물+동+호 유일), `contracts`가 계약(기간+임대인+임차인) 단위 — 같은 호실도 계약이 바뀌면 새 `contracts` row가 생성되어 이전 임차인 데이터와 분리됨.
- 초대코드는 계약 1건당 발급, 1회용(`used_at`), 7일 만료(`expires_at`).

## 스모크 테스트

```bash
python smoke_test.py
```

가입→건물/호실/계약 생성→초대코드→임차인가입→로그인 전체 플로우와 주요 실패 케이스(중복 호실, 재사용 초대코드, 오답 비밀번호, 권한 없는 접근)를 한번에 검증.
