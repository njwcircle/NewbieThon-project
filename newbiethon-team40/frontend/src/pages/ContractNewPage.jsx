import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import HeroHeader from '../components/HeroHeader'
import TextField from '../components/TextField'
import Button from '../components/Button'

const EMPTY = {
  buildingName: '',
  address: '',
  dong: '',
  ho: '',
  rentAmount: '',
  maintenanceFeeFixed: '',
  startDate: '',
  endDate: '',
}

// 필수값은 백엔드 스키마 기준입니다.
// building.address / unit.ho / contract.rent_amount, maintenance_fee_fixed, start_date, end_date
const REQUIRED = ['address', 'ho', 'rentAmount', 'maintenanceFeeFixed', 'startDate', 'endDate']

export default function ContractNewPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { addUnit } = useData()
  const [form, setForm] = useState(EMPTY)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user.role !== 'LANDLORD') return <Navigate to="/" replace />

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })
  const ready = REQUIRED.every((key) => form[key].trim() !== '')

  // 건물 → 호실 → 계약 → 초대코드 순으로 4번의 API 호출이 일어납니다.
  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const created = await addUnit(form)
      navigate('/contracts/new/done', {
        replace: true,
        state: {
          code: created.inviteCode,
          expiresAt: created.expiresAt,
          label: `${form.buildingName.trim() || form.address.trim()} ${form.ho.trim()}호`,
        },
      })
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <HeroHeader title="계약 등록" subtitle="임차인과 공유할 계약 정보를 입력해주세요" />

      <div className="auth-form">
        <TextField
          label="건물 이름 (선택)"
          placeholder="예) 고려빌라"
          value={form.buildingName}
          onChange={set('buildingName')}
        />
        <TextField
          label="주소"
          placeholder="예) 서울시 마포구 월드컵북로 123"
          value={form.address}
          onChange={set('address')}
        />

        <div className="field-row">
          <TextField label="동 (선택)" placeholder="A동" value={form.dong} onChange={set('dong')} />
          <TextField label="호수" placeholder="301" value={form.ho} onChange={set('ho')} />
        </div>

        <TextField
          label="월세"
          inputMode="numeric"
          suffix="원"
          placeholder="750000"
          value={form.rentAmount}
          onChange={set('rentAmount')}
        />
        <TextField
          label="관리비"
          inputMode="numeric"
          suffix="원"
          placeholder="50000"
          value={form.maintenanceFeeFixed}
          onChange={set('maintenanceFeeFixed')}
        />

        <div className="field-row">
          <TextField label="계약 시작일" type="date" value={form.startDate} onChange={set('startDate')} />
          <TextField label="계약 종료일" type="date" value={form.endDate} onChange={set('endDate')} />
        </div>

        <p className="result-note">🔑 등록을 완료하면 임차인 초대코드가 발급돼요</p>

        {error && <p className="field-error">{error}</p>}

        <Button full disabled={!ready || loading} onClick={submit}>
          {loading ? '등록 중…' : '계약 등록하기'}
        </Button>
      </div>

      <div style={{ height: 40 }} />
    </div>
  )
}
