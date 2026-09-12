import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, RESPONSIBLE, formatDate, formatWon } from '../constants'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import StatusChip from '../components/StatusChip'
import ChipGroup from '../components/ChipGroup'
import TextField from '../components/TextField'
import Button from '../components/Button'
import PhotoUpload from '../components/PhotoUpload'
import { uploadReceiptImage } from '../api/data'
import { assetUrl } from '../api/client'

const PAYER_OPTIONS = [
  { value: 'LANDLORD', label: '임대인' },
  { value: 'TENANT', label: '임차인' },
  { value: 'SHARED', label: '분담' },
]

export default function IssueDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { issues, resolveIssue } = useData()

  const issue = issues.find((i) => i.id === id)
  const [detail, setDetail] = useState('')
  const [cost, setCost] = useState('')
  const [payer, setPayer] = useState(issue?.responsible === 'TENANT' ? 'TENANT' : 'LANDLORD')
  const [receiptUrl, setReceiptUrl] = useState(null)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  if (!issue) return <Navigate to="/issues" replace />

  const isLandlord = user.role === 'LANDLORD'
  const canResolve = isLandlord && issue.status !== 'RESOLVED'

  const submit = async () => {
    setError('')
    setSaving(true)
    try {
      await resolveIssue(issue, { detail, cost, payer, receiptUrl })
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page page--gray">
      <PageHeader title="문제 해결 기록" />

      <div className="page-body stack gap-12" style={{ paddingTop: 8 }}>
        <Card>
          <div className="detail-head">
            <div>
              <p className="detail-title">{CATEGORY[issue.category]} 문제</p>
              <p className="detail-sub">{issue.unitLabel}</p>
              <p className="detail-dates">
                접수 {formatDate(issue.createdAt)}
                {issue.resolvedAt && ` · 완료 ${formatDate(issue.resolvedAt)}`}
              </p>
            </div>
            <StatusChip status={issue.status} />
          </div>

          {issue.description && <p className="detail-answer mt-16">{issue.description}</p>}
          {issue.photoUrl && <img className="photo-attached" src={assetUrl(issue.photoUrl)} alt="접수 사진" />}
        </Card>

        <Card>
          <p className="form-label">해결 정보</p>

          <p className="detail-q">누가 부담하나요?</p>
          <ChipGroup
            options={PAYER_OPTIONS}
            value={canResolve ? payer : issue.payer || issue.responsible}
            onChange={canResolve ? setPayer : () => {}}
            variant="pill"
          />

          <p className="detail-q mt-24">어떻게 해결했나요?</p>
          {issue.resolvedDetail ? (
            <p className="detail-answer">{issue.resolvedDetail}</p>
          ) : canResolve ? (
            <>
              <textarea
                className="textarea"
                placeholder="어떻게 해결했는지 적어주세요"
                value={detail}
                onChange={(e) => setDetail(e.target.value)}
              />
              <div className="mt-16">
                <TextField
                  label="수리 비용"
                  inputMode="numeric"
                  suffix="원"
                  placeholder="0"
                  value={cost}
                  onChange={(e) => setCost(e.target.value)}
                />
              </div>
              <div className="mt-16">
                <p className="detail-q">영수증 (선택)</p>
                <PhotoUpload
                  value={receiptUrl}
                  onChange={setReceiptUrl}
                  upload={uploadReceiptImage}
                  label="영수증 첨부"
                />
              </div>
            </>
          ) : (
            <p className="detail-answer text-gray">아직 해결 내용이 등록되지 않았어요</p>
          )}
        </Card>

        {issue.cost != null && (
          <Card>
            <p className="form-label">결제 정보</p>
            <p className="detail-q">비용</p>
            <p className="detail-cost">{formatWon(issue.cost)}</p>

            <p className="detail-q mt-24">결제 상태</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <StatusChip status={issue.paymentStatus} />
            </div>

            <p className="detail-q mt-16">부담자</p>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <StatusChip label={RESPONSIBLE[issue.payer] || '분담'} tone="muted" />
            </div>

            {issue.receiptImageUrl && (
              <>
                <p className="detail-q mt-24">영수증</p>
                <img className="photo-attached" src={assetUrl(issue.receiptImageUrl)} alt="영수증" />
              </>
            )}
          </Card>
        )}

        {error && <p className="field-error">{error}</p>}

        {canResolve && (
          <Button full disabled={!detail.trim() || saving} onClick={submit}>
            {saving ? '처리 중…' : '해결 처리하기'}
          </Button>
        )}

        <Button variant="outline" full onClick={() => navigate(`/chat/${issue.contractId}`)}>
          채팅으로 문의하기
        </Button>
      </div>

      <div style={{ height: 32 }} />
    </div>
  )
}
