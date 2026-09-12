import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, formatDate } from '../mock/constants'
import StatusChip from '../components/StatusChip'

const timeOf = (iso) => {
  const [h, m] = iso.slice(11, 16).split(':').map(Number)
  const ampm = h < 12 ? '오전' : '오후'
  const hour = h % 12 === 0 ? 12 : h % 12
  return `${ampm} ${hour}:${String(m).padStart(2, '0')}`
}

export default function ChatRoomPage() {
  const { roomId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { rooms, messages, issues, sendMessage } = useData()
  const [text, setText] = useState('')
  const bottomRef = useRef(null)

  const room = rooms.find((r) => r.id === roomId)
  const list = messages[roomId] || []

  // 새 메시지가 오면 항상 맨 아래를 보여줍니다.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [list.length])

  if (!room) return <Navigate to="/chat" replace />

  const isLandlord = user.role === 'LANDLORD'
  const counterpart = isLandlord ? `${room.tenantName} 임차인` : `${room.landlordName} 임대인`

  const submit = (e) => {
    e.preventDefault()
    if (!text.trim()) return
    sendMessage(roomId, text.trim())
    setText('')
  }

  return (
    <div className="page page--fixed">
      <header className="chat-head">
        <button type="button" className="pagehead-back" onClick={() => navigate('/chat')} aria-label="뒤로">
          ‹
        </button>
        <span className="chat-avatar">{counterpart.slice(0, 1)}</span>
        <div>
          <p className="chat-name">{counterpart}</p>
        </div>
      </header>

      <div className="chat-body">
        <span className="chat-day">{formatDate(list[0]?.sentAt.slice(0, 10))}</span>

        {list.map((msg) => {
          const mine = msg.senderId === user.id
          const issue = msg.type === 'issue' ? issues.find((i) => i.id === msg.issueId) : null

          return (
            <div key={msg.id} className={`msg${mine ? ' msg--me' : ''}`}>
              {issue ? (
                <div className="msg-issue">
                  <div className="listcard-top">
                    <span className="msg-issue-title">{issue.title}</span>
                    <StatusChip status={issue.status} />
                  </div>
                  <p className="msg-issue-meta">
                    {CATEGORY[issue.category]} · {formatDate(issue.createdAt)}
                  </p>
                </div>
              ) : (
                <p className="msg-bubble">{msg.text}</p>
              )}
              <span className="msg-time">{timeOf(msg.sentAt)}</span>
            </div>
          )
        })}

        <div ref={bottomRef} />
      </div>

      <form className="chat-composer" onSubmit={submit}>
        <input
          className="chat-input"
          placeholder="메시지를 입력하세요"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <button type="submit" className="chat-send" disabled={!text.trim()} aria-label="전송">
          →
        </button>
      </form>
    </div>
  )
}
