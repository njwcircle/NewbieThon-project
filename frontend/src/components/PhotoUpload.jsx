import { useState } from 'react'
import { assetUrl } from '../api/client'

/*
 * 파일을 고르면 바로 서버에 올리고, 돌려받은 경로(value)를 부모에게 넘깁니다.
 * upload는 uploadIssueImage / uploadReceiptImage 중 하나를 받습니다.
 */
export default function PhotoUpload({ value, onChange, upload, label = '사진 추가' }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const pick = async (e) => {
    const file = e.target.files?.[0]
    e.target.value = '' // 같은 파일을 다시 골라도 동작하도록 초기화
    if (!file) return

    setBusy(true)
    setError('')
    try {
      const { url } = await upload(file)
      onChange(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (value) {
    return (
      <div className="photo-preview">
        <img src={assetUrl(value)} alt="첨부한 사진" />
        <button type="button" className="photo-remove" onClick={() => onChange(null)} aria-label="사진 삭제">
          ✕
        </button>
      </div>
    )
  }

  return (
    <>
      <label className="photo-add">
        <input type="file" accept="image/*" hidden onChange={pick} disabled={busy} />
        <span className="photo-add-plus">{busy ? '⏳' : '＋'}</span>
        {busy ? '올리는 중…' : label}
      </label>
      {error && <p className="field-error mt-16">{error}</p>}
    </>
  )
}
