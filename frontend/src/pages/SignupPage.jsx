import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../store'
import { formatPhone } from '../constants'
import HeroHeader from '../components/HeroHeader'
import SegmentedControl from '../components/SegmentedControl'
import TextField from '../components/TextField'
import Button from '../components/Button'

const ROLES = [
  { value: 'TENANT', label: '임차인' },
  { value: 'LANDLORD', label: '임대인' },
]

export default function SignupPage() {
  const navigate = useNavigate()
  const { signup } = useAuth()
  const [role, setRole] = useState('TENANT')
  const [form, setForm] = useState({ name: '', phone: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const mismatch = form.confirm.length > 0 && form.password !== form.confirm
  const tooShort = form.password.length > 0 && form.password.length < 8
  const ready = form.name && form.phone && form.password.length >= 8 && form.password === form.confirm

  // 임차인은 가입 직후 계약이 없으므로 AppLayout이 /invite로 보냅니다.
  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      await signup(role, form.name.trim(), formatPhone(form.phone), form.password.trim())
      navigate('/', { replace: true })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <HeroHeader
        title="회원가입"
        subtitle={
          role === 'TENANT'
            ? '가입 후 임대인에게 받은 초대코드를 입력하면 계약이 연결돼요'
            : '가입 후 보유하신 세대의 계약을 등록할 수 있어요'
        }
      />

      <div className="auth-form">
        <SegmentedControl options={ROLES} value={role} onChange={setRole} />
        <TextField label="이름" placeholder="예) 김민재" value={form.name} onChange={set('name')} />
        <TextField
          label="전화번호"
          type="tel"
          placeholder="010-0000-0000"
          value={form.phone}
          onChange={set('phone')}
        />
        <TextField
          label="비밀번호"
          type="password"
          placeholder="8자 이상 입력하세요"
          value={form.password}
          onChange={set('password')}
          error={tooShort ? '비밀번호는 8자 이상이어야 해요' : ''}
        />
        <TextField
          label="비밀번호 확인"
          type="password"
          placeholder="비밀번호를 한 번 더 입력하세요"
          value={form.confirm}
          onChange={set('confirm')}
          error={mismatch ? '비밀번호가 일치하지 않아요' : error}
        />
        <Button full disabled={!ready || loading} onClick={submit}>
          {loading ? '가입 중…' : '가입하기'}
        </Button>
      </div>

      <p className="auth-footer">
        이미 계정이 있으신가요?{' '}
        <Link to="/login">
          <strong>로그인</strong>
        </Link>
      </p>
    </div>
  )
}
