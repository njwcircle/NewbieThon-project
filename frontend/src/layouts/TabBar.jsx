import { NavLink } from 'react-router-dom'
import { useAuth } from '../store'
import { HomeIcon, IssueIcon, ChatIcon, ProfileIcon, GridIcon } from '../components/icons'

// 탭 구성은 역할에 따라 2번째 항목만 달라집니다.
const LANDLORD_TABS = [
  { to: '/', Icon: HomeIcon, label: '홈' },
  { to: '/units', Icon: GridIcon, label: '세대' },
  { to: '/chat', Icon: ChatIcon, label: '채팅' },
  { to: '/mypage', Icon: ProfileIcon, label: '프로필' },
]

const TENANT_TABS = [
  { to: '/', Icon: HomeIcon, label: '홈' },
  { to: '/issues', Icon: IssueIcon, label: '문제접수' },
  { to: '/chat', Icon: ChatIcon, label: '채팅' },
  { to: '/mypage', Icon: ProfileIcon, label: '프로필' },
]

export default function TabBar() {
  const { user } = useAuth()
  const tabs = user.role === 'LANDLORD' ? LANDLORD_TABS : TENANT_TABS

  return (
    <nav className="tabbar">
      {tabs.map(({ to, Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          className={({ isActive }) => `tabbar-item${isActive ? ' tabbar-item--on' : ''}`}
        >
          <span className="tabbar-icon">
            <Icon />
          </span>
          <span className="tabbar-label">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
