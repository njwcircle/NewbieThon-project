import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, CATEGORY_LIST } from '../constants'
import PageHeader from '../components/PageHeader'
import ChipGroup from '../components/ChipGroup'
import PhotoUpload from '../components/PhotoUpload'
import { uploadIssueImage } from '../api/data'
import Button from '../components/Button'

const OPTIONS = CATEGORY_LIST.map((value) => ({ value, label: CATEGORY[value] }))

export default function IssueNewPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { addIssue } = useData()
  const [category, setCategory] = useState(null)
  const [description, setDescription] = useState('')
  const [photoUrl, setPhotoUrl] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user.role !== 'TENANT') return <Navigate to="/" replace />

  // 사전합의 매칭 판단은 서버가 합니다. 결과를 그대로 다음 화면으로 넘깁니다.
  const submit = async () => {
    setError('')
    setLoading(true)
    try {
      const result = await addIssue({ contractId: user.contractId, category, description, photoUrl })
      navigate('/issues/new/done', { replace: true, state: result })
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <PageHeader title="문제접수" />

      <div className="form-section">
        <span className="form-label">어떤 문제가 있나요?</span>
        <ChipGroup options={OPTIONS} value={category} onChange={setCategory} />
      </div>

      <div className="form-section">
        <span className="form-label">상태를 설명해주세요</span>
        <textarea
          className="textarea"
          placeholder={'어떤 문제가 있는지 자세히 설명해주세요\n(예: 보일러에서 이상한 소리가 나요)'}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>

      <div className="form-section">
        <span className="form-label">사진 첨부</span>
        <PhotoUpload value={photoUrl} onChange={setPhotoUrl} upload={uploadIssueImage} />
        <p className="form-hint">jpg · png · webp · gif, 최대 10MB</p>
        <p className="form-hint">• 접수하시면 임대인에게 즉시 알림이 전송돼요</p>
      </div>

      <div className="form-actions">
        {error && <p className="field-error mt-16" style={{ marginBottom: 12 }}>{error}</p>}
        <Button full disabled={!category || !description.trim() || loading} onClick={submit}>
          {loading ? '접수 중…' : '접수하기'}
        </Button>
      </div>
    </div>
  )
}
