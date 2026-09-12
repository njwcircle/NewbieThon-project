// 백엔드에 채팅 API가 아직 없습니다. 연결할 때 서버 작업이 별도로 필요합니다.
// rooms: 임대인은 임차인 수만큼, 임차인은 임대인 1명
export const rooms = [
  {
    id: 'r1',
    contractId: 'c1',
    landlordName: '박서연',
    tenantName: '김민재',
    unitLabel: '마포 월드컵북로 123 301호',
    lastMessage: '확인했습니다! 이상없이 잘 작동해요',
    lastAt: '2026-09-10T16:30',
    unread: 0,
  },
  {
    id: 'r2',
    contractId: 'c2',
    landlordName: '박서연',
    tenantName: '이서연',
    unitLabel: '서대문 연희로 45 2층',
    lastMessage: '도어락 수리 비용은 누가 부담하나요?',
    lastAt: '2026-09-08T11:02',
    unread: 2,
  },
  {
    id: 'r3',
    contractId: 'c3',
    landlordName: '박서연',
    tenantName: '박도윤',
    unitLabel: '은평 통일로 890 A동 102호',
    lastMessage: '네 감사합니다',
    lastAt: '2026-08-30T09:14',
    unread: 0,
  },
]

// senderId: 'u1' = 임대인(박서연), 'u2' = 임차인
export const messages = {
  r1: [
    {
      id: 'm1',
      senderId: 'u1',
      type: 'text',
      text: '안녕하세요! 보일러 수리 기사님이 내일 오전 10시에 방문 예정입니다',
      sentAt: '2026-09-10T14:10',
    },
    { id: 'm2', senderId: 'u2', type: 'text', text: '네 알겠습니다 감사합니다!', sentAt: '2026-09-10T14:12' },
    { id: 'm3', senderId: 'u1', type: 'issue', issueId: 'i1', sentAt: '2026-09-10T14:13' },
    {
      id: 'm4',
      senderId: 'u1',
      type: 'text',
      text: '수리 완료되면 사진이랑 함께 알려주세요~',
      sentAt: '2026-09-10T14:15',
    },
    {
      id: 'm5',
      senderId: 'u2',
      type: 'text',
      text: '확인했습니다! 이상없이 잘 작동해요',
      sentAt: '2026-09-10T16:30',
    },
  ],
  r2: [
    {
      id: 'm6',
      senderId: 'u2',
      type: 'text',
      text: '도어락이 가끔 안 열려요. 접수했습니다',
      sentAt: '2026-09-08T10:55',
    },
    { id: 'm7', senderId: 'u2', type: 'issue', issueId: 'i5', sentAt: '2026-09-08T10:56' },
    {
      id: 'm8',
      senderId: 'u2',
      type: 'text',
      text: '도어락 수리 비용은 누가 부담하나요?',
      sentAt: '2026-09-08T11:02',
    },
  ],
  r3: [
    { id: 'm9', senderId: 'u1', type: 'text', text: '관리비 정산 내역 보내드렸습니다', sentAt: '2026-08-30T09:10' },
    { id: 'm10', senderId: 'u2', type: 'text', text: '네 감사합니다', sentAt: '2026-08-30T09:14' },
  ],
}
