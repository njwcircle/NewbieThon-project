export default function EmptyState({ icon = '📭', title, desc, children }) {
  return (
    <div className="empty">
      <span className="empty-icon">{icon}</span>
      <p className="empty-title">{title}</p>
      {desc && <p className="empty-desc">{desc}</p>}
      {children}
    </div>
  )
}
