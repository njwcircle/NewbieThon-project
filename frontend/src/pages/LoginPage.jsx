import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import HeroHeader from '../components/HeroHeader'
import SegmentedControl from '../components/SegmentedControl'
import TextField from '../components/TextField'
import Button from '../components/Button'

const ROLES = [
  { value: 'TENANT', label: '임차인' },
  { value: 'LANDLORD', label: '임대인' },
]

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, logout } = useAuth()
  const [role, setRole] = useState('TENANT')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const me = await login(phone, password)
      // 역할은 서버가 정합니다. 탭을 잘못 고른 경우 알려주고 되돌립니다.
      if (me.role !== role) {
        logout()
        setError(`이 계정은 ${me.role === 'LANDLORD' ? '임대인' : '임차인'} 계정이에요`)
        return
      }
      navigate('/', { replace: true })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <HeroHeader brand={'주거\n주거'} eyebrow="임대인과 임차인을 위한 스마트 관리" title="로그인" />

      <div className="auth-form">
        <SegmentedControl options={ROLES} value={role} onChange={setRole} />
        <TextField
          label="전화번호"
          type="tel"
          placeholder="010-0000-0000"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        <TextField
          label="비밀번호"
          type="password"
          placeholder="비밀번호를 입력하세요"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={error}
        />

        <div className="stack gap-8">
          <Button full disabled={loading || !phone || !password} onClick={submit}>
            {loading ? '로그인 중…' : '로그인'}
          </Button>
          <Button variant="outline" full small onClick={() => navigate('/signup')}>
            회원가입
          </Button>
        </div>
      </div>
    </div>
  )
}
