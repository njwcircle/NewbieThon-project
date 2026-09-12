import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import HeroHeader from '../components/HeroHeader'
import Button from '../components/Button'

export default function InvitePage() {
  const navigate = useNavigate()
  const { joinContract, logout } = useAuth()
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      await joinContract(code)
      navigate('/', { replace: true })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <HeroHeader title="초대코드 입력" subtitle="임대인에게 받은 8자리 코드를 입력하면 계약이 연결돼요" />

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

        <Button full disabled={code.length < 8 || loading} onClick={submit}>
          {loading ? '연결 중…' : '계약 연결하기'}
        </Button>
      </div>

      <p className="auth-footer">
        <button type="button" onClick={logout}>
          다른 계정으로 로그인
        </button>
      </p>
    </div>
  )
}
