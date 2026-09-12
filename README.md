# NewbieThon-project

## 사전합의사항 ↔ 문제접수 데이터 인터페이스

대시보드(사전합의사항 저장)와 문제접수(자동해결 분기 판단) 간 연동 규격. 필드/값이 바뀌면 이 문서도 같이 업데이트할 것.

### 1. 카테고리 코드값

| 표시명 | 코드값 |
|---|---|
| 보일러 | `BOILER` |
| 수도 | `WATER` |
| 전기 | `ELECTRIC` |
| 벽 | `WALL` |
| 가구 | `FURNITURE` |
| 기타(자유입력) | `ETC` |

### 2. 부담주체 코드값

| 표시명 | 코드값 |
|---|---|
| 임대인 부담 | `LANDLORD` |
| 임차인 부담 | `TENANT` |
| 협의 필요(사전합의 없음) | `UNDEFINED` |

### 3. 사전합의사항 데이터 스키마

대시보드가 아래 형태로 내려준다. 키는 `contractId`(계약 단위) 기준.

```json
{
  "contractId": "계약ID",
  "agreements": [
    {
      "category": "BOILER",
      "responsible": "LANDLORD",
      "note": "노후 보일러 고장 시 임대인 부담 (특약 3조)"
    },
    {
      "category": "FURNITURE",
      "responsible": "TENANT",
      "note": "가구 파손은 임차인 부담"
    }
  ]
}
```

### 4. 매칭 로직 (v1)

- 문제접수의 `category`가 `agreements`의 `category`와 일치하면 → 해당 `responsible` 값 사용
- 일치하는 항목 없으면 → `UNDEFINED` 취급 → 채팅으로 넘어가는 분기
- 사진/상세설명 기반 예외 판단은 v1 범위 밖 (추후 고도화)

### 5. 조회 방식

- 문제접수 화면에서 카테고리 선택 시 `contractId`로 사전합의 목록 조회 → 매칭 → 자동해결 안내 표시
- 백엔드가 하나로 공유되면 테이블 직접 조회, 서비스가 분리되면 API 호출 (팀 구조 확정되면 명시)

### 확정 사항 (v1 기준, 팀원과 다르게 논의되면 갱신)

- [x] 카테고리 6종(`BOILER`/`WATER`/`ELECTRIC`/`WALL`/`FURNITURE`/`ETC`)으로 확정. 추가 필요 시 코드값만 늘리면 되므로 이번 스프린트는 이대로 진행.
- [x] 필드명(`contractId`, `category`, `responsible`, `note`) 그대로 사용.
- [x] 조회 방식은 **DB 직접 조회**로 확정. 백엔드를 팀에서 하나로 공유하는 구조라 API 계층을 따로 둘 이유가 없음. 추후 서비스가 분리되면 그때 API로 전환.
