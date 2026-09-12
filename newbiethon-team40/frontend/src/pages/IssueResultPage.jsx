import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useData } from '../store'
import { RESPONSIBLE } from '../mock/constants'
import Button from '../components/Button'

/*
 * 접수 직후 화면. 사전 협의내용에 같은 카테고리가 있으면 부담자가 자동 확정되고,
 * 없으면 임대인과 채팅으로 협의하도록 안내합니다. (README 매칭 규칙 v1)
 */
export default function IssueResultPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { issues } = useData()

  const issue = issues.find((i) => i.id === location.state?.issueId)
  if (!issue) return <Navigate to="/issues" replace />

  const matched = issue.status === 'AUTO_RESOLVED'

  return (
    <div className="page">
      <div className="result">
        <span className="result-icon">{matched ? '✅' : '💬'}</span>
        <h1 className="result-title">{matched ? '접수가 완료됐어요' : '협의가 필요해요'}</h1>
        <p className="result-desc">
          {matched ? (
            <>
              사전 협의내용에 따라
              <br />
              <strong>{RESPONSIBLE[issue.responsible]} 부담</strong>으로 확인됐어요
            </>
          ) : (
            <>
              사전에 협의된 내용이 없어요.
              <br />
              임대인과 채팅으로 부담자를 정해주세요
            </>
          )}
        </p>

        {matched && issue.matchedNote && <p className="result-note">📄 {issue.matchedNote}</p>}
      </div>

      <div className="form-actions stack gap-12">
        {matched ? (
          <Button full onClick={() => navigate(`/issues/${issue.id}`, { replace: true })}>
            접수 내역 보기
          </Button>
        ) : (
          <Button full onClick={() => navigate('/chat', { replace: true })}>
            채팅으로 이동
          </Button>
        )}
        <Button variant="outline" full onClick={() => navigate('/', { replace: true })}>
          홈으로
        </Button>
      </div>
    </div>
  )
}
