export default function InfoRow({ label, value }) {
  return (
    <div className="inforow">
      <span className="inforow-label">{label}</span>
      <span className="inforow-value">{value}</span>
    </div>
  )
}
