export default function SectionHeader({ title, actionLabel, onAction, blue = false }) {
  return (
    <div className="sectionhead">
      <h2 className="sectionhead-title">{title}</h2>
      {actionLabel && (
        <button
          type="button"
          className={`sectionhead-action${blue ? ' sectionhead-action--blue' : ''}`}
          onClick={onAction}
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
