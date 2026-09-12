import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { formatDate } from '../constants'
import HeroHeader from '../components/HeroHeader'
import Button from '../components/Button'

export default function InviteCodePage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [copied, setCopied] = useState(false)

  const { code, expiresAt, label } = location.state || {}
  if (!code) return <Navigate to="/units" replace />

  const copy = () => {
    navigator.clipboard?.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="page">
      <HeroHeader title="등록 완료" subtitle={`${label} 계약이 등록됐어요`} />

      <div className="auth-form">
        <div className="code-display">
          <span className="contract-card-label">임차인 초대코드</span>
          <span className="code-display-value">{code}</span>
          <span className="code-display-expire">
            {expiresAt ? `${formatDate(expiresAt.slice(0, 10))}까지 유효해요` : '발급일로부터 7일간 유효해요'}
          </span>
        </div>

        <p className="result-note">
          임차인이 회원가입 후 이 코드를 입력하면 계약이 연결되고, 같은 대시보드를 함께 보게 됩니다.
        </p>

        <Button variant="outline" full onClick={copy}>
          {copied ? '복사했어요' : '초대코드 복사하기'}
        </Button>
        <Button full onClick={() => navigate('/units', { replace: true })}>
          세대 목록으로
        </Button>
      </div>

      <div style={{ height: 40 }} />
    </div>
  )
}
