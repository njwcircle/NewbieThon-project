import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../store'
import TabBar from './TabBar'

// 탭바가 있는 화면(홈 · 세대 · 접수내역 · 채팅 · 마이페이지)의 공통 껍데기.
// 로그인 여부와 임차인의 계약 연결 여부를 여기서 한 번만 검사합니다.
export default function AppLayout() {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) return <Navigate to="/login" replace />

  // 임차인은 초대코드로 계약에 연결되기 전까지 볼 수 있는 데이터가 없습니다.
  if (user.role === 'TENANT' && !user.contractId && location.pathname !== '/mypage') {
    return <Navigate to="/invite" replace />
  }

  return (
    <>
      <Outlet />
      <TabBar />
    </>
  )
}
