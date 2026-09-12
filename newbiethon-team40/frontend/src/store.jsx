import { createContext, useContext, useState } from 'react'
import { LANDLORD, TENANT, DEMO_INVITE_CODE, DEMO_INVITE_CONTRACT_ID } from './mock/users'
import { units as mockUnits, vendors as mockVendors, agreements as mockAgreements } from './mock/units'
import { issues as mockIssues } from './mock/issues'
import { rooms as mockRooms, messages as mockMessages } from './mock/chat'

/*
 * 백엔드를 붙이기 전까지 앱의 모든 데이터를 여기서 들고 있습니다.
 * 나중에는 각 함수 안을 fetch 호출로 바꾸기만 하면 됩니다.
 */
const AuthContext = createContext(null)
const DataContext = createContext(null)

export const useAuth = () => useContext(AuthContext)
export const useData = () => useContext(DataContext)

const STORAGE_KEY = 'homecheck.user'
const randomCode = () => Math.random().toString(16).slice(2, 10).toUpperCase()
const today = () => new Date().toISOString().slice(0, 10)

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  })

  const [units, setUnits] = useState(mockUnits)
  const [issues, setIssues] = useState(mockIssues)
  const [vendors, setVendors] = useState(mockVendors)
  const [agreements, setAgreements] = useState(mockAgreements)
  const [rooms] = useState(mockRooms)
  const [messages, setMessages] = useState(mockMessages)

  const save = (next) => {
    setUser(next)
    if (next) localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    else localStorage.removeItem(STORAGE_KEY)
  }

  /* ===== 인증 ===== */
  // mock 단계에서는 비밀번호를 검사하지 않고 역할만 정합니다.
  const login = (role) => save(role === 'LANDLORD' ? { ...LANDLORD } : { ...TENANT })

  const logout = () => save(null)

  // 임차인이 초대코드를 입력해 계약에 연결됩니다. 맞으면 true.
  const joinContract = (code) => {
    if (code.trim().toUpperCase() !== DEMO_INVITE_CODE) return false
    save({ ...user, contractId: DEMO_INVITE_CONTRACT_ID })
    return true
  }

  /* ===== 계약 · 세대 ===== */
  const addUnit = (form) => {
    const inviteCode = randomCode()
    const unit = {
      unitId: `un${units.length + 1}`,
      contractId: `c${units.length + 1}`,
      buildingName: form.buildingName || form.address,
      address: form.address,
      dong: form.dong || null,
      ho: form.ho,
      tenantName: null,
      tenantPhone: null,
      rentAmount: Number(form.rentAmount),
      maintenanceFeeFixed: Number(form.maintenanceFeeFixed),
      startDate: form.startDate,
      endDate: form.endDate,
      state: 'PENDING',
      inviteCode,
    }
    setUnits((prev) => [unit, ...prev])
    return unit
  }

  /* ===== 문제 접수 ===== */
  // 사전 협의내용에서 같은 카테고리를 찾아 부담자를 자동 판정합니다.
  const matchAgreement = (contractId, category) =>
    agreements.find((a) => a.contractId === contractId && a.category === category) || null

  const addIssue = ({ contractId, unitLabel, category, title, description }) => {
    const matched = matchAgreement(contractId, category)
    const issue = {
      id: `i${Date.now()}`,
      contractId,
      unitLabel,
      category,
      title,
      description,
      photoUrl: null,
      status: matched ? 'AUTO_RESOLVED' : 'IN_CHAT',
      responsible: matched ? matched.responsible : 'UNDEFINED',
      matchedNote: matched ? matched.note : null,
      resolvedDetail: null,
      cost: null,
      paymentStatus: null,
      payer: null,
      createdAt: today(),
      resolvedAt: null,
    }
    setIssues((prev) => [issue, ...prev])
    return issue
  }

  const resolveIssue = (id, detail) =>
    setIssues((prev) =>
      prev.map((it) =>
        it.id === id ? { ...it, status: 'RESOLVED', resolvedDetail: detail, resolvedAt: today() } : it,
      ),
    )

  /* ===== 채팅 ===== */
  const sendMessage = (roomId, text) => {
    const msg = {
      id: `m${Date.now()}`,
      senderId: user.id,
      type: 'text',
      text,
      sentAt: new Date().toISOString().slice(0, 16),
    }
    setMessages((prev) => ({ ...prev, [roomId]: [...(prev[roomId] || []), msg] }))
  }

  const auth = { user, login, logout, joinContract }
  const data = {
    units,
    issues,
    vendors,
    agreements,
    rooms,
    messages,
    addUnit,
    addIssue,
    resolveIssue,
    matchAgreement,
    setVendors,
    setAgreements,
    sendMessage,
  }

  return (
    <AuthContext.Provider value={auth}>
      <DataContext.Provider value={data}>{children}</DataContext.Provider>
    </AuthContext.Provider>
  )
}
