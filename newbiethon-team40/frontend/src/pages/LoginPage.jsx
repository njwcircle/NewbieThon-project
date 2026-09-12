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
  const { login } = useAuth()
  const [role, setRole] = useState('TENANT')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')

  // mock 단계에서는 비밀번호를 검사하지 않고 선택한 역할로 바로 로그인합니다.
  const submit = () => {
    login(role)
    navigate('/', { replace: true })
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
        />
        <div className="stack gap-8">
          <Button full onClick={submit}>
            로그인
          </Button>
          <Button variant="outline" full small onClick={() => navigate('/signup')}>
            회원가입
          </Button>
        </div>
      </div>
    </div>
  )
}
