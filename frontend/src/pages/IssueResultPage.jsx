import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { RESPONSIBLE } from '../constants'
import Button from '../components/Button'

/*
 * 접수 직후 화면. 서버가 사전합의를 찾아서 agreement_matched / next_action으로 알려줍니다.
 *  - FOLLOW_AGREEMENT : 합의된 부담자로 확정
 *  - OPEN_CHAT        : 합의 없음 → 채팅으로 협의
 */
export default function IssueResultPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const result = location.state

  if (!result) return <Navigate to="/issues" replace />

  const matched = result.matched

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
              <strong>{RESPONSIBLE[result.responsible]} 부담</strong>으로 확인됐어요
            </>
          ) : (
            <>
              사전에 협의된 내용이 없어요.
              <br />
              임대인과 채팅으로 부담자를 정해주세요
            </>
          )}
        </p>

        {matched && result.note && <p className="result-note">📄 {result.note}</p>}
      </div>

      <div className="form-actions stack gap-12">
        {matched ? (
          <Button full onClick={() => navigate(`/issues/${result.issueId}`, { replace: true })}>
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
