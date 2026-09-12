import { useNavigate } from 'react-router-dom'

export default function PageHeader({ title, to }) {
  const navigate = useNavigate()
  const goBack = () => (to ? navigate(to) : navigate(-1))

  return (
    <header className="pagehead">
      <button type="button" className="pagehead-back" onClick={goBack} aria-label="뒤로">
        ‹
      </button>
      <h1 className="pagehead-title">{title}</h1>
    </header>
  )
}
