// 백엔드 enum ↔ 화면 한글 라벨. 문구를 바꾸려면 여기만 고치세요.

export const CATEGORY = {
  BOILER: '보일러',
  WATER: '수도',
  ELECTRIC: '전기',
  WALL: '벽',
  FURNITURE: '가구',
  ETC: '기타',
}

export const CATEGORY_LIST = Object.keys(CATEGORY)

export const RESPONSIBLE = {
  LANDLORD: '임대인',
  TENANT: '임차인',
  UNDEFINED: '미정',
}

// tone: progress(연한 파랑) | done(진한 인디고) | alert(빨강) | muted(회색)
export const ISSUE_STATUS = {
  RECEIVED: { label: '접수중', tone: 'progress' },
  AUTO_RESOLVED: { label: '접수완료', tone: 'progress' },
  IN_CHAT: { label: '협의중', tone: 'progress' },
  RESOLVED: { label: '해결완료', tone: 'done' },
}

export const UNIT_STATE = {
  OCCUPIED: { label: '입주중', tone: 'progress' },
  PENDING: { label: '초대코드 대기', tone: 'muted' },
  ISSUE: { label: '문제 접수', tone: 'alert' },
  VACANT: { label: '공실', tone: 'muted' },
}

export const PAYMENT_STATUS = {
  PENDING: { label: '결제대기', tone: 'muted' },
  PAID: { label: '결제완료', tone: 'done' },
}

export const formatWon = (n) => (n == null ? '-' : `${n.toLocaleString('ko-KR')}원`)

export const formatManwon = (n) => (n == null ? '-' : `${Math.round(n / 10000)}만원`)

export const formatDate = (iso) => (iso ? iso.replaceAll('-', '.') : '-')
