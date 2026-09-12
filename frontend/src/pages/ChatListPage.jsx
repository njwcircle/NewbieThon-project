import { useNavigate } from 'react-router-dom'
import { useData } from '../store'
import ListCard from '../components/ListCard'
import EmptyState from '../components/EmptyState'

export default function ChatListPage() {
  const navigate = useNavigate()
  const { rooms, loading } = useData()

  return (
    <div className="page page--tabbed">
      <h1 className="page-title">채팅</h1>

      <div className="page-body stack gap-12">
        {rooms.length === 0 ? (
          <EmptyState
            icon="💬"
            title={loading ? '불러오는 중…' : '대화가 없어요'}
            desc={loading ? '' : '임차인이 계약에 연결되면 채팅방이 만들어집니다'}
          />
        ) : (
          rooms.map((room) => (
            <ListCard
              key={room.id}
              title={room.counterpartName}
              meta={[room.unitLabel, room.lastMessage].filter(Boolean).join('\n')}
              onClick={() => navigate(`/chat/${room.id}`)}
            />
          ))
        )}
      </div>

      <div style={{ height: 24 }} />
    </div>
  )
}
