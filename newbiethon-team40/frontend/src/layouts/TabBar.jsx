import { NavLink } from 'react-router-dom'
import { useAuth } from '../store'

// 탭 구성은 역할에 따라 2번째 항목만 달라집니다.
const LANDLORD_TABS = [
  { to: '/', icon: '🏠', label: '홈' },
  { to: '/units', icon: '🏢', label: '세대' },
  { to: '/chat', icon: '💬', label: '채팅' },
  { to: '/mypage', icon: '👤', label: '프로필' },
]

const TENANT_TABS = [
  { to: '/', icon: '🏠', label: '홈' },
  { to: '/issues', icon: '📝', label: '문제접수' },
  { to: '/chat', icon: '💬', label: '채팅' },
  { to: '/mypage', icon: '👤', label: '프로필' },
]

export default function TabBar() {
  const { user } = useAuth()
  const tabs = user.role === 'LANDLORD' ? LANDLORD_TABS : TENANT_TABS

  return (
    <nav className="tabbar">
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end={tab.to === '/'}
          className={({ isActive }) => `tabbar-item${isActive ? ' tabbar-item--on' : ''}`}
        >
          <span className="tabbar-icon">{tab.icon}</span>
          <span className="tabbar-label">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
