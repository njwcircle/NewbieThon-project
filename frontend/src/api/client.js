/*
 * 모든 API 호출이 거쳐가는 곳.
 * - 로그인 토큰을 자동으로 헤더에 붙인다
 * - 에러 응답을 한국어 메시지로 통일한다
 * - 서버 주소는 .env의 VITE_API_URL로 바꿀 수 있다 (배포 시)
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'homecheck.token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)

export const setToken = (token) => {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

// 토큰이 만료됐을 때 앱 전체를 로그아웃시키기 위한 콜백 (store.jsx에서 등록)
let onUnauthorized = null
export const setUnauthorizedHandler = (fn) => {
  onUnauthorized = fn
}

// FastAPI는 유효성 에러를 {detail: [{msg, loc}]} 배열로, 그 외는 {detail: "문자열"}로 준다
function readMessage(data, status) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return `요청을 처리하지 못했어요. (${status})`
}

async function request(method, path, body) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(BASE_URL + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, '서버에 연결할 수 없어요. 백엔드가 실행 중인지 확인해주세요.')
  }

  if (res.status === 204) return null

  const text = await res.text()
  const data = text ? JSON.parse(text) : null

  if (!res.ok) {
    if (res.status === 401) {
      setToken(null)
      onUnauthorized?.()
    }
    throw new ApiError(res.status, readMessage(data, res.status))
  }
  return data
}

/*
 * 파일 업로드는 JSON이 아니라 multipart라서 따로 둡니다.
 * Content-Type은 브라우저가 경계값(boundary)까지 넣어 자동으로 만들어주므로 직접 지정하면 안 됩니다.
 */
export async function uploadFile(path, file) {
  const form = new FormData()
  form.append('file', file)

  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(BASE_URL + path, { method: 'POST', headers, body: form })
  } catch {
    throw new ApiError(0, '서버에 연결할 수 없어요. 백엔드가 실행 중인지 확인해주세요.')
  }

  const text = await res.text()
  const data = text ? JSON.parse(text) : null
  if (!res.ok) throw new ApiError(res.status, readMessage(data, res.status))
  return data
}

// 서버는 "/uploads/issues/abc.jpg" 같은 상대경로를 주므로 앞에 서버 주소를 붙여야 보입니다.
export const assetUrl = (path) => (path ? `${BASE_URL}${path}` : null)

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  put: (path, body) => request('PUT', path, body),
  patch: (path, body) => request('PATCH', path, body),
  del: (path) => request('DELETE', path),
}
