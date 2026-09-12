// 딤 배경을 누르면 닫힙니다. 시트 안을 누를 때는 닫히지 않도록 클릭을 막습니다.
export default function BottomSheet({ open, onClose, title, chip, children }) {
  if (!open) return null

  return (
    <div className="sheet-dim" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-handle" />
        <div className="sheet-head">
          <h2 className="sheet-title">{title}</h2>
          {chip}
          <button type="button" className="sheet-close" onClick={onClose} aria-label="닫기">
            ✕
          </button>
        </div>
        <div className="sheet-divider" />
        {children}
      </div>
    </div>
  )
}
