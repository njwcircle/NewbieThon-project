import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import { DEMO_INVITE_CODE } from '../mock/users'
import HeroHeader from '../components/HeroHeader'
import Button from '../components/Button'

export default function InvitePage() {
  const navigate = useNavigate()
  const { joinContract, logout } = useAuth()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')

  const submit = () => {
    if (joinContract(code)) navigate('/', { replace: true })
    else setError('초대코드가 올바르지 않거나 만료되었어요')
  }

  return (
    <div className="page">
      <HeroHeader
        title="초대코드 입력"
        subtitle="임대인에게 받은 8자리 코드를 입력하면 계약이 연결돼요"
      />

      <div className="auth-form">
        <div>
          <input
            className="code-input"
            maxLength={8}
            placeholder="ABCD1234"
            value={code}
            onChange={(e) => {
              setCode(e.target.value)
              setError('')
            }}
          />
          {error && <p className="field-error mt-16">{error}</p>}
        </div>

        <Button full disabled={code.length < 8} onClick={submit}>
          계약 연결하기
        </Button>

        <p className="caption text-center">데모용 코드: {DEMO_INVITE_CODE}</p>
      </div>

      <p className="auth-footer">
        <button type="button" onClick={logout}>
          다른 계정으로 로그인
        </button>
      </p>
    </div>
  )
}
