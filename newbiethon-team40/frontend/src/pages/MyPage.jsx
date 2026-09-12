import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { formatDate } from '../mock/constants'
import Card from '../components/Card'
import StatusChip from '../components/StatusChip'
import Toggle from '../components/Toggle'

export default function MyPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { units } = useData()
  const [alerts, setAlerts] = useState({ payment: true, issue: true, chat: false })

  const isLandlord = user.role === 'LANDLORD'
  const unit = units.find((u) => u.contractId === user.contractId)

  const setAlert = (key) => (on) => setAlerts({ ...alerts, [key]: on })

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
                {isLandlord ? `총 ${units.length}세대 보유` : unit ? `${unit.buildingName} ${unit.ho}호` : '계약 없음'}
              </p>
            </div>
          </div>
        </Card>

        <Card>
          <p className="my-group-label">계정</p>
          <button type="button" className="my-item">
            계정 로그인
            <span className="my-item-value">{user.phone} ›</span>
          </button>
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
              <button type="button" className="my-item">
                현재 계약
                <span className="my-item-value">
                  {unit ? `${formatDate(unit.startDate)} ~ ${formatDate(unit.endDate)}` : '-'} ›
                </span>
              </button>
              <button type="button" className="my-item" onClick={() => navigate('/invite')}>
                초대코드 입력
                <span className="my-item-value">›</span>
              </button>
            </>
          )}
          <button type="button" className="my-item">
            지난 계약
            <span className="my-item-value">›</span>
          </button>
        </Card>

        <Card>
          <p className="my-group-label">알림 설정</p>
          <div className="my-item">
            납부 알림
            <Toggle on={alerts.payment} onChange={setAlert('payment')} />
          </div>
          <div className="my-item">
            문제접수 알림
            <Toggle on={alerts.issue} onChange={setAlert('issue')} />
          </div>
          <div className="my-item">
            일반 채팅
            <Toggle on={alerts.chat} onChange={setAlert('chat')} />
          </div>
        </Card>

        <button type="button" className="my-logout" onClick={logout}>
          로그아웃
        </button>
      </div>
    </div>
  )
}
