import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider, useAuth } from './store'
import AppLayout from './layouts/AppLayout'
import PlainLayout from './layouts/PlainLayout'

import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import InvitePage from './pages/InvitePage'
import HomePage from './pages/HomePage'
import UnitsPage from './pages/UnitsPage'
import ContractNewPage from './pages/ContractNewPage'
import InviteCodePage from './pages/InviteCodePage'
import IssueListPage from './pages/IssueListPage'
import IssueNewPage from './pages/IssueNewPage'
import IssueResultPage from './pages/IssueResultPage'
import IssueDetailPage from './pages/IssueDetailPage'
import ChatListPage from './pages/ChatListPage'
import ChatRoomPage from './pages/ChatRoomPage'
import MyPage from './pages/MyPage'

function AppRoutes() {
  const { booting } = useAuth()

  // 저장된 토큰으로 로그인 상태를 복구하는 동안은 아무것도 그리지 않습니다.
  // (이게 없으면 잠깐 로그인 화면이 깜빡였다가 홈으로 넘어갑니다)
  if (booting) return <div className="page" />

  return (
    <Routes>
      {/* 로그인 전 */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* 탭바 있는 화면 */}
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/units" element={<UnitsPage />} />
        <Route path="/issues" element={<IssueListPage />} />
        <Route path="/chat" element={<ChatListPage />} />
        <Route path="/mypage" element={<MyPage />} />
      </Route>

      {/* 탭바 없는 전체화면 */}
      <Route element={<PlainLayout />}>
        <Route path="/invite" element={<InvitePage />} />
        <Route path="/contracts/new" element={<ContractNewPage />} />
        <Route path="/contracts/new/done" element={<InviteCodePage />} />
        <Route path="/issues/new" element={<IssueNewPage />} />
        <Route path="/issues/new/done" element={<IssueResultPage />} />
        <Route path="/issues/:id" element={<IssueDetailPage />} />
        <Route path="/chat/:roomId" element={<ChatRoomPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <div className="app-shell">
          <AppRoutes />
        </div>
      </BrowserRouter>
    </AppProvider>
  )
}
