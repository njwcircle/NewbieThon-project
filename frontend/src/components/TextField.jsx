export default function TextField({ label, suffix, error, ...rest }) {
  return (
    <label className="field">
      {label && <span className="field-label">{label}</span>}
      <span className="field-box">
        <input className="field-input" {...rest} />
        {suffix && <span className="field-suffix">{suffix}</span>}
      </span>
      {error && <span className="field-error">{error}</span>}
    </label>
  )
}
