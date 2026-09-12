import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { getNotificationSettings, updateNotificationSettings, unitLabelOf } from '../api/data'
import { formatDate } from '../constants'
import Card from '../components/Card'
import StatusChip from '../components/StatusChip'
import Toggle from '../components/Toggle'

const ALERTS = [
  { key: 'payment_alert', label: '납부 알림' },
  { key: 'issue_alert', label: '문제접수 알림' },
  { key: 'chat_alert', label: '일반 채팅' },
]

export default function MyPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { units } = useData()
  const [alerts, setAlerts] = useState(null)

  useEffect(() => {
    getNotificationSettings()
      .then(setAlerts)
      .catch(() => setAlerts({ payment_alert: true, issue_alert: true, chat_alert: true }))
  }, [])

  const isLandlord = user.role === 'LANDLORD'
  const unit = units.find((u) => u.contractId === user.contractId)
  const contracts = user.contracts || []

  // 토글은 먼저 화면에 반영하고, 실패하면 되돌립니다.
  const toggle = (key) => (on) => {
    const prev = alerts
    const next = { ...alerts, [key]: on }
    setAlerts(next)
    updateNotificationSettings(next).catch(() => setAlerts(prev))
  }

  return (
    <div className="page page--tabbed page--gray">
      <h1 className="page-title">마이페이지</h1>

      <div className="page-body stack gap-12">
        <Card>
          <div className="my-profile">
            <span className="my-avatar">{user.name.slice(0, 1)}</span>
            <div>
              <p className="my-name">
                {user.name}
                <StatusChip label={isLandlord ? '임대인' : '임차인'} tone="progress" />
              </p>
              <p className="my-sub">
                {isLandlord
                  ? `총 ${units.length}세대 보유`
                  : unit
                    ? unitLabelOf(unit)
                    : '연결된 계약 없음'}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <p className="my-group-label">계정</p>
          <div className="my-item">
            계정 로그인
            <span className="my-item-value">{user.phone}</span>
          </div>
          <button type="button" className="my-item">
            비밀번호 변경
            <span className="my-item-value">›</span>
          </button>
        </Card>

        <Card>
          <p className="my-group-label">계약</p>
          {isLandlord ? (
            <button type="button" className="my-item" onClick={() => navigate('/units')}>
              보유 세대
              <span className="my-item-value">{units.length}세대 ›</span>
            </button>
          ) : (
            <>
              <div className="my-item">
                현재 계약
                <span className="my-item-value">
                  {unit ? `${formatDate(unit.startDate)} ~ ${formatDate(unit.endDate)}` : '-'}
                </span>
              </div>
              <button type="button" className="my-item" onClick={() => navigate('/invite')}>
                초대코드 입력
                <span className="my-item-value">›</span>
              </button>
            </>
          )}
          <div className="my-item">
            {isLandlord ? '등록한 계약' : '지난 계약'}
            <span className="my-item-value">{contracts.length}건</span>
          </div>
        </Card>

        <Card>
          <p className="my-group-label">알림 설정</p>
          {ALERTS.map(({ key, label }) => (
            <div key={key} className="my-item">
              {label}
              <Toggle on={alerts?.[key] ?? false} onChange={toggle(key)} />
            </div>
          ))}
        </Card>

        <button type="button" className="my-logout" onClick={logout}>
          로그아웃
        </button>
      </div>
    </div>
  )
}
