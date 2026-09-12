# Frontend (React)

임대인/임차인 계약 관리 앱의 웹 프론트엔드. Vite + React + React Router.
백엔드(`../backend`)의 FastAPI 서버에 직접 붙어서 동작하며, 목업 데이터는 없다.

## 실행 방법

**백엔드가 먼저 떠 있어야 한다.** 프론트만 띄우면 모든 화면이 "서버에 연결할 수 없어요"로 뜬다.

```bash
# 터미널 1 — 백엔드
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # JWT_SECRET_KEY를 반드시 채울 것 (없으면 서버가 시작되지 않음)
uvicorn app.main:app --reload      # http://127.0.0.1:8000

# 터미널 2 — 프론트
cd frontend
npm install
npm run dev                        # http://localhost:5173
```

Node 18 이상이면 된다(개발은 22.19에서 했다). `npm run build`로 배포용 빌드를 만들고, `npm run preview`로 빌드 결과를 확인할 수 있다.

### 백엔드 주소 바꾸기

기본값은 `http://127.0.0.1:8000`이다. 배포 서버에 붙이려면 `frontend/.env`를 만들고:

```
VITE_API_URL=https://배포된-백엔드-주소
```

`.env`는 gitignore되어 있다. 참고용 양식은 `.env.example`에 있다.
업로드된 이미지 경로도 이 값을 따라가므로 여기만 바꾸면 된다.

## 계정 만들기

DB가 비어 있으면 아무것도 보이지 않는다. 회원가입 화면에서 직접 만들면 된다.

1. **임대인**으로 가입 → 계약 등록(건물·호실·월세·관리비·계약기간) → **초대코드**가 발급된다
2. **임차인**으로 가입 → 로그인하면 초대코드 입력 화면으로 자동 이동 → 위 코드 입력 → 계약 연결

임차인은 초대코드를 넣기 전까지 볼 수 있는 데이터가 없어서, 다른 화면에 들어갈 수 없다(`AppLayout`이 `/invite`로 돌려보낸다).

## 화면 구성

| 경로 | 화면 | 역할 |
|---|---|---|
| `/login` `/signup` | 로그인 · 회원가입 | 공통 |
| `/invite` | 초대코드 입력 | 임차인 |
| `/` | 홈 (역할에 따라 다른 내용) | 공통 |
| `/units` | 세대 대시보드 + 상세 바텀시트 | 임대인 |
| `/contracts/new` `/contracts/new/done` | 계약 등록 · 초대코드 발급 | 임대인 |
| `/issues` `/issues/new` `/issues/new/done` `/issues/:id` | 접수 내역 · 접수 · 결과 · 상세 | 공통/임차인 |
| `/chat` `/chat/:roomId` | 채팅 목록 · 채팅방 | 공통 |
| `/mypage` | 마이페이지 | 공통 |

**역할별로 라우트를 나누지 않았다.** 같은 페이지를 쓰고 세 군데에서만 분기한다 — 홈의 내용, 탭바 메뉴, 페이지 안의 일부 버튼(예: 임대인만 "해결 처리하기").

## 폴더 구조

```
src/
├── main.jsx            진입점, CSS 로드
├── App.jsx             라우터 + 레이아웃 분배
├── store.jsx           로그인 상태 + 서버 데이터를 한곳에서 관리 (Context)
├── constants.js        enum ↔ 한글 라벨, 금액/날짜 포맷
├── api/
│   ├── client.js       fetch 래퍼 (토큰, 에러, 업로드)
│   ├── auth.js         인증 엔드포인트
│   └── data.js         나머지 엔드포인트 + 응답 변환 + 복합 로더
├── components/         재사용 UI 14개
├── layouts/            AppLayout(탭바 O) / PlainLayout(탭바 X) / TabBar
├── pages/              화면 14개
└── styles/
    ├── tokens.css      색·반경 등 디자인 토큰 ← 색을 바꾸려면 여기만
    ├── base.css        리셋 + 레이아웃 유틸
    ├── components.css  공통 컴포넌트 스타일
    └── pages.css       화면별 스타일
```

CSS Modules나 Tailwind를 쓰지 않고 **일반 CSS 4개 파일**로 나눴다. 클래스 이름을 한 파일에서 찾아볼 수 있는 쪽이 읽기 쉽다고 판단했다.

## 데이터가 흐르는 방식

```
pages ──useData()──> store.jsx ──> api/data.js ──> api/client.js ──> 백엔드
```

- 로그인하면 `store`의 `refresh()`가 **필요한 데이터를 한 번에 전부** 받아온다(건물·세대·문제·협의사항·수리업체·메시지). 이후 화면 이동은 서버 호출 없이 즉시 뜬다.
- 쓰기 작업(계약 등록, 문제 접수, 해결 처리 등) 뒤에는 다시 `refresh()`를 호출해 서버와 맞춘다.
- 그래서 각 페이지에는 `useEffect`로 데이터를 불러오는 코드가 없다. `useData()`에서 꺼내 쓰기만 하면 된다.

### 백엔드에 없어서 프론트가 만들어내는 값

API 문서를 봐도 없는 필드들이라, 아래는 `api/data.js`에서 계산한다.

| 값 | 계산 방식 |
|---|---|
| 세대 상태 배지 | 계약 없으면 `VACANT`, 임차인 미연결이면 `PENDING`, 미해결 문제가 있으면 `ISSUE`, 나머지 `OCCUPIED` |
| 전체 세대 목록 | `GET /buildings` → 건물마다 `GET /buildings/{id}/board` → 합침 (전체 조회 API가 없음) |
| 채팅방 목록 | 계약 목록에서 파생. **채팅방 id = 계약 id** (목록 API가 없음) |
| 문제 제목 | `description`을 제목으로 사용 (`title` 필드가 없음) |
| 임차인 관점 건물명 | board에는 동·호수만 있어서 `GET /contracts/{id}`로 보강 |

### API를 새로 붙일 때

1. `api/data.js`에 한 줄 추가 — `export const getX = (id) => api.get(\`/x/${id}\`)`
2. 응답 필드가 `snake_case`라면 같은 파일에 변환 함수를 두고 `camelCase`로 바꾼다
3. `store.jsx`에 함수를 추가하고, 서버 상태를 바꾸는 작업이면 마지막에 `await refresh()`
4. 페이지에서 `useData()`로 꺼내 쓴다

토큰 첨부·에러 메시지·401 처리는 `client.js`가 전부 하므로 신경 쓰지 않아도 된다.

## 아직 연결되지 않은 것

- **납부/월세 화면** — 백엔드에는 `/contracts/{id}/payments`가 있지만 화면을 만들지 않았다(v1 범위 제외). 세대 상세의 "납부 상태" 배지만 표시한다.
- **알림 목록** — 홈 우상단 벨 아이콘에 연결된 화면이 없다. `/notifications/due-payments` 활용 가능.
- **비밀번호 변경** — 마이페이지에 항목만 있고 동작하지 않는다. `PATCH /auth/password` 사용하면 된다.
- **임차인 연락처** — `BoardRow` 응답에 `tenant_phone`이 없어서 세대 상세에서 뺐다. 백엔드에 필드가 추가되면 표시할 수 있다.
- **FCM 푸시** — 웹에서는 사용하지 않는다.
- 사진은 **문제당 1장**만 가능하다. `issue_reports.photo_url`이 단일 컬럼이라서다.

## 배포

백엔드는 Railway에 올라가 있다. 프론트는 정적 빌드라 Vercel이나 Netlify 어디든 된다.

**호스팅 설정**

| 항목 | 값 |
|---|---|
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| 환경변수 | `VITE_API_URL` = Railway 백엔드 주소 |

`VITE_API_URL`은 **빌드 시점에 코드에 박히는** 값이다. 주소를 바꾸면 다시 배포해야 반영된다.

**SPA 라우팅** — `vercel.json`(Vercel)과 `public/_redirects`(Netlify)가 이미 들어있다.
이 설정이 없으면 주소창에 `/units`를 직접 치거나 새로고침할 때 404가 난다.
서버가 `/units`라는 파일을 찾으려 하기 때문이고, 위 설정이 모든 경로를 `index.html`로 넘겨서
라우팅을 React Router가 처리하게 한다.

**주의 — Railway의 파일시스템은 재시작하면 초기화된다**

백엔드가 SQLite(`app.db`)와 업로드 이미지를 로컬 파일로 저장하고 있어서,
서버가 재시작되면 **가입한 계정·계약·채팅·사진이 전부 사라진다.**
데모용이면 감수해도 되지만, 계속 쓸 거라면 Postgres(`DATABASE_URL` 교체)와
이미지 외부 저장소가 필요하다.

## 참고

- 전체 API 목록: [`../backend/API.md`](../backend/API.md)
- 백엔드 실행·스키마: [`../backend/README.md`](../backend/README.md)
