import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../store'

// 탭바 없이 전체화면으로 뜨는 화면(계약 등록 · 문제 접수 · 상세 · 채팅방)용.
export default function PlainLayout() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}
