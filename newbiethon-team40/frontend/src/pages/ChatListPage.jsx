import { useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import ListCard from '../components/ListCard'
import StatusChip from '../components/StatusChip'
import EmptyState from '../components/EmptyState'

export default function ChatListPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { rooms } = useData()

  const isLandlord = user.role === 'LANDLORD'
  const myRooms = isLandlord ? rooms : rooms.filter((r) => r.contractId === user.contractId)

  return (
    <div className="page page--tabbed">
      <h1 className="page-title">채팅</h1>

      <div className="page-body stack gap-12">
        {myRooms.length === 0 ? (
          <EmptyState icon="💬" title="대화가 없어요" desc="문제를 접수하면 채팅방이 만들어집니다" />
        ) : (
          myRooms.map((room) => (
            <ListCard
              key={room.id}
              title={isLandlord ? `${room.tenantName} 임차인` : `${room.landlordName} 임대인`}
              meta={`${room.unitLabel}\n${room.lastMessage}`}
              right={room.unread > 0 ? <StatusChip label={String(room.unread)} tone="alert" /> : null}
              onClick={() => navigate(`/chat/${room.id}`)}
            />
          ))
        )}
      </div>

      <div style={{ height: 24 }} />
    </div>
  )
}
