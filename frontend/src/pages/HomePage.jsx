import { useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { formatDate } from '../constants'
import { unitLabelOf } from '../api/data'
import { PinIcon, GridIcon } from '../components/icons'
import SectionHeader from '../components/SectionHeader'
import ListCard from '../components/ListCard'
import StatusChip from '../components/StatusChip'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'

function TenantHome() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { units, issues, loading } = useData()

  const unit = units.find((u) => u.contractId === user.contractId)
  const myIssues = issues.filter((i) => i.contractId === user.contractId).slice(0, 2)

  return (
    <>
      <div className="home-head">
        <div>
          <h1 className="home-greeting">안녕하세요, {user.name}님</h1>
          <p className="home-place">
            <PinIcon /> {unit ? unitLabelOf(unit) : '연결된 계약 없음'}
          </p>
        </div>
      </div>

      {unit && (
        <div className="home-section">
          <div className="contract-card">
            <p className="contract-card-label">현재 계약</p>
            <p className="contract-card-title">{unitLabelOf(unit)}</p>
            <p className="contract-card-period">
              {formatDate(unit.startDate)} ~ {formatDate(unit.endDate)}
            </p>
            <button type="button" className="contract-link" onClick={() => navigate('/mypage')}>
              계약 정보 보기 ▸
            </button>
          </div>
        </div>
      )}

      <div className="home-section">
        <SectionHeader title="문제접수" actionLabel="전체보기" onAction={() => navigate('/issues')} />

        <div className="stack gap-12">
          <div className="cta-card">
            <div>
              <p className="cta-card-title">문제가 발생했나요?</p>
              <p className="cta-card-desc">보일러, 수도, 전기 등 문제를 접수해보세요</p>
            </div>
            <Button small onClick={() => navigate('/issues/new')}>
              접수하기
            </Button>
          </div>

          {myIssues.map((issue) => (
            <ListCard
              key={issue.id}
              title={issue.title}
              meta={formatDate(issue.createdAt)}
              right={<StatusChip status={issue.status} />}
              onClick={() => navigate(`/issues/${issue.id}`)}
            />
          ))}
        </div>
      </div>

      <div style={{ height: 32 }} />
    </>
  )
}

function LandlordHome() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { units, issues, loading } = useData()

  const openIssues = issues.filter((i) => i.status !== 'RESOLVED')
  const recent = [...openIssues, ...issues.filter((i) => i.status === 'RESOLVED')].slice(0, 3)

  // 접수 카드에 임차인 이름을 함께 보여주기 위해 계약으로 세대를 찾습니다.
  const tenantOf = (contractId) => units.find((u) => u.contractId === contractId)?.tenantName

  return (
    <>
      <div className="home-head">
        <div>
          <h1 className="home-greeting">안녕하세요, {user.name}님</h1>
          <p className="home-place">총 {units.length}세대 ▾</p>
        </div>
      </div>

      <div className="home-section">
        <div className="dash-card">
          <button type="button" className="dash-inner" onClick={() => navigate('/units')}>
            <span className="dash-icon">
              <GridIcon />
            </span>
            <span className="dash-label">세대입주 대시보드</span>
            <span className="dash-arrow">▶</span>
          </button>
        </div>
      </div>

      <div className="home-section">
        <SectionHeader title="문제접수 현황" actionLabel="전체보기" onAction={() => navigate('/issues')} />

        {recent.length === 0 ? (
          <EmptyState icon="🙌" title={loading ? '불러오는 중…' : '접수된 문제가 없어요'} desc={loading ? '' : '임차인이 문제를 접수하면 여기에 표시됩니다'} />
        ) : (
          <div className="stack gap-12">
            {recent.map((issue) => (
              <div key={issue.id} className="issue-card">
                <button
                  type="button"
                  style={{ width: '100%', textAlign: 'left' }}
                  onClick={() => navigate(`/issues/${issue.id}`)}
                >
                  <div className="listcard-top">
                    <span className="listcard-title">
                      {issue.unitLabel} · {issue.title}
                    </span>
                    <StatusChip status={issue.status} />
                  </div>
                  <p className="issue-card-meta">
                    {[tenantOf(issue.contractId), formatDate(issue.createdAt)].filter(Boolean).join(' · ')}
                  </p>
                </button>

                {issue.status !== 'RESOLVED' && (
                  <div className="issue-card-action">
                    <Button full small onClick={() => navigate(`/issues/${issue.id}`)}>
                      해결 처리하기
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ height: 32 }} />
    </>
  )
}

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div className="page page--tabbed">
      {user.role === 'LANDLORD' ? <LandlordHome /> : <TenantHome />}
    </div>
  )
}
