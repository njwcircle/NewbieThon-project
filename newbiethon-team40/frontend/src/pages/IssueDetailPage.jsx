import { useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, RESPONSIBLE, formatDate, formatWon } from '../mock/constants'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import StatusChip from '../components/StatusChip'
import ChipGroup from '../components/ChipGroup'
import Button from '../components/Button'

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
  const [detail, setDetail] = useState('')

  const issue = issues.find((i) => i.id === id)
  if (!issue) return <Navigate to="/issues" replace />

  const isLandlord = user.role === 'LANDLORD'
  const canResolve = isLandlord && issue.status !== 'RESOLVED'

  return (
    <div className="page page--gray">
      <PageHeader title="문제 해결 기록" />

      <div className="page-body stack gap-12" style={{ paddingTop: 8 }}>
        <Card>
          <div className="detail-head">
            <div>
              <p className="detail-title">{issue.title}</p>
              <p className="detail-sub">
                {issue.unitLabel} · {CATEGORY[issue.category]}
              </p>
              <p className="detail-dates">
                접수 {formatDate(issue.createdAt)}
                {issue.resolvedAt && ` · 완료 ${formatDate(issue.resolvedAt)}`}
              </p>
            </div>
            <StatusChip status={issue.status} />
          </div>
        </Card>

        <Card>
          <p className="form-label">해결 정보</p>

          <p className="detail-q">누가 부담하나요?</p>
          <ChipGroup
            options={PAYER_OPTIONS}
            value={issue.responsible}
            onChange={() => {}}
            variant="pill"
          />

          <p className="detail-q mt-24">어떻게 해결했나요?</p>
          {issue.resolvedDetail ? (
            <p className="detail-answer">{issue.resolvedDetail}</p>
          ) : canResolve ? (
            <textarea
              className="textarea"
              placeholder="어떻게 해결했는지 적어주세요"
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
            />
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
              <StatusChip label={RESPONSIBLE[issue.payer] || '-'} tone="muted" />
            </div>
          </Card>
        )}

        {canResolve && (
          <Button full disabled={!detail.trim()} onClick={() => resolveIssue(issue.id, detail)}>
            해결 처리하기
          </Button>
        )}

        <Button variant="outline" full onClick={() => navigate('/chat')}>
          채팅으로 문의하기
        </Button>
      </div>

      <div style={{ height: 32 }} />
    </div>
  )
}
