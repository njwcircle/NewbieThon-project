import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, formatDate, formatWon } from '../mock/constants'
import ChipGroup from '../components/ChipGroup'
import ListCard from '../components/ListCard'
import StatusChip from '../components/StatusChip'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'

const FILTERS = [
  { value: 'ALL', label: '전체' },
  { value: 'OPEN', label: '진행중' },
  { value: 'RESOLVED', label: '해결완료' },
]

export default function IssueListPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { issues } = useData()
  const [filter, setFilter] = useState('ALL')

  const isLandlord = user.role === 'LANDLORD'
  const mine = isLandlord ? issues : issues.filter((i) => i.contractId === user.contractId)
  const list = mine.filter((i) => {
    if (filter === 'OPEN') return i.status !== 'RESOLVED'
    if (filter === 'RESOLVED') return i.status === 'RESOLVED'
    return true
  })

  return (
    <div className="page page--tabbed">
      <h1 className="page-title">{isLandlord ? '접수 현황' : '접수 내역'}</h1>

      <div className="filter-bar">
        <ChipGroup options={FILTERS} value={filter} onChange={setFilter} variant="pill" />
      </div>

      <div className="page-body stack gap-12">
        {!isLandlord && (
          <Button full onClick={() => navigate('/issues/new')}>
            ＋ 문제 접수하기
          </Button>
        )}

        {list.length === 0 ? (
          <EmptyState icon="🗂️" title="접수된 문제가 없어요" desc="새로운 문제가 접수되면 여기에 표시됩니다" />
        ) : (
          list.map((issue) => (
            <ListCard
              key={issue.id}
              title={isLandlord ? `${issue.unitLabel} · ${issue.title}` : issue.title}
              meta={[
                CATEGORY[issue.category],
                formatDate(issue.createdAt),
                issue.cost != null ? formatWon(issue.cost) : null,
              ]
                .filter(Boolean)
                .join(' · ')}
              right={<StatusChip status={issue.status} />}
              onClick={() => navigate(`/issues/${issue.id}`)}
            />
          ))
        )}
      </div>

      <div style={{ height: 24 }} />
    </div>
  )
}
