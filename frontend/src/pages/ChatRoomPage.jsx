import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { CATEGORY, formatDate } from '../constants'
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
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  const room = rooms.find((r) => r.id === roomId)
  const list = messages[roomId] || []

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [list.length])

  if (!room) return <Navigate to="/chat" replace />

  const submit = async (e) => {
    e.preventDefault()
    if (!text.trim() || sending) return
    const content = text.trim()
    setText('')
    setSending(true)
    try {
      await sendMessage(roomId, content)
    } catch {
      setText(content) // 실패하면 입력값을 되돌려줍니다
    } finally {
      setSending(false)
    }
  }

  let lastDay = null

  return (
    <div className="page page--fixed">
      <header className="chat-head">
        <button type="button" className="pagehead-back" onClick={() => navigate('/chat')} aria-label="뒤로">
          ‹
        </button>
        <span className="chat-avatar">{room.counterpartName.slice(0, 1)}</span>
        <div>
          <p className="chat-name">{room.counterpartName}</p>
        </div>
      </header>

      <div className="chat-body">
        {list.map((msg) => {
          const day = msg.sentAt.slice(0, 10)
          const showDay = day !== lastDay
          lastDay = day

          const mine = msg.senderId === user.id
          const isSystem = msg.senderId === null
          const issue = msg.type === 'SYSTEM_ISSUE' ? issues.find((i) => i.id === msg.refId) : null

          return (
            <div key={msg.id} style={{ display: 'contents' }}>
              {showDay && <span className="chat-day">{formatDate(day)}</span>}

              {isSystem ? (
                <div className="msg-system">
                  <p className="msg-system-text">{msg.content}</p>
                  {issue && (
                    <button
                      type="button"
                      className="msg-issue-link"
                      onClick={() => navigate(`/issues/${issue.id}`)}
                    >
                      <span className="msg-issue-title">{CATEGORY[issue.category]} 문제</span>
                      <StatusChip status={issue.status} />
                    </button>
                  )}
                </div>
              ) : (
                <div className={`msg${mine ? ' msg--me' : ''}`}>
                  <p className="msg-bubble">{msg.content}</p>
                  <span className="msg-time">{timeOf(msg.sentAt)}</span>
                </div>
              )}
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
        <button type="submit" className="chat-send" disabled={!text.trim() || sending} aria-label="전송">
          →
        </button>
      </form>
    </div>
  )
}
