export default function Toggle({ on, onChange }) {
  return (
    <button
      type="button"
      className={`toggle${on ? ' toggle--on' : ''}`}
      onClick={() => onChange(!on)}
      aria-pressed={on}
    >
      <span className="toggle-knob" />
    </button>
  )
}
