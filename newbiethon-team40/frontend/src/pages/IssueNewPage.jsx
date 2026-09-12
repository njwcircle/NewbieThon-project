import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, CATEGORY_LIST } from '../mock/constants'
import PageHeader from '../components/PageHeader'
import ChipGroup from '../components/ChipGroup'
import Button from '../components/Button'

const OPTIONS = CATEGORY_LIST.map((value) => ({ value, label: CATEGORY[value] }))

export default function IssueNewPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { units, addIssue } = useData()
  const [category, setCategory] = useState(null)
  const [description, setDescription] = useState('')

  if (user.role !== 'TENANT') return <Navigate to="/" replace />

  const unit = units.find((u) => u.contractId === user.contractId)

  const submit = () => {
    const issue = addIssue({
      contractId: user.contractId,
      unitLabel: unit ? `${unit.buildingName} ${unit.ho}호` : '',
      category,
      title: `${CATEGORY[category]} 문제`,
      description,
    })
    navigate('/issues/new/done', { replace: true, state: { issueId: issue.id } })
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
        <button type="button" className="photo-add">
          <span className="photo-add-plus">＋</span>
          사진 추가
        </button>
        <p className="form-hint">최대 5장까지 첨부할 수 있어요</p>
        <p className="form-hint">• 접수하시면 임대인에게 즉시 알림이 전송돼요</p>
      </div>

      <div className="form-actions">
        <Button full disabled={!category} onClick={submit}>
          접수하기
        </Button>
      </div>
    </div>
  )
}
