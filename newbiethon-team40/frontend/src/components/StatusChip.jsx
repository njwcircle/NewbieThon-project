import { ISSUE_STATUS, UNIT_STATE, PAYMENT_STATUS } from '../constants'

// status 코드만 넘기면 라벨과 색을 알아서 찾습니다.
// 예) <StatusChip status="RESOLVED" /> <StatusChip status="VACANT" />
export default function StatusChip({ status, label, tone }) {
  const found = ISSUE_STATUS[status] || UNIT_STATE[status] || PAYMENT_STATUS[status]
  const text = label ?? found?.label ?? status
  const color = tone ?? found?.tone ?? 'muted'

  if (!text) return null
  return <span className={`chip chip--${color}`}>{text}</span>
}
