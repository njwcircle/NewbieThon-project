// 홈 · 접수 내역 · 세대 대시보드 · 채팅 목록이 전부 이 카드 한 종류입니다.
export default function ListCard({ title, meta, right, onClick }) {
  const Tag = onClick ? 'button' : 'div'

  return (
    <Tag className="listcard" onClick={onClick} type={onClick ? 'button' : undefined}>
      <div className="listcard-top">
        <span className="listcard-title">{title}</span>
        {right}
      </div>
      {meta && <p className="listcard-meta">{meta}</p>}
    </Tag>
  )
}
