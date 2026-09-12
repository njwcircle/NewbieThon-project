import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as authApi from './api/auth'
import * as dataApi from './api/data'
import { getToken, setToken, setUnauthorizedHandler } from './api/client'

/*
 * 앱의 모든 서버 데이터를 여기 한 곳에서 들고 있습니다.
 * 로그인하면 refresh()가 필요한 걸 전부 받아오고, 쓰기 작업 뒤에도 refresh()로 다시 맞춥니다.
 */
const AuthContext = createContext(null)
const DataContext = createContext(null)

export const useAuth = () => useContext(AuthContext)
export const useData = () => useContext(DataContext)

const STORAGE_KEY = 'homecheck.user'

const EMPTY = { units: [], issues: [], agreements: [], vendors: [], messages: {} }

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  })
  const [booting, setBooting] = useState(() => Boolean(getToken()))
  const [data, setData] = useState(EMPTY)
  const [loading, setLoading] = useState(false)

  const save = (next) => {
    setUser(next)
    if (next) localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    else localStorage.removeItem(STORAGE_KEY)
    if (!next) setData(EMPTY)
  }

  /* ===== 데이터 ===== */

  const refresh = useCallback(async (who) => {
    const target = who ?? JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
    if (!target) return
    setLoading(true)
    try {
      const loaded =
        target.role === 'LANDLORD' ? await dataApi.loadLandlordData() : await dataApi.loadTenantData()
      setData(loaded)
    } finally {
      setLoading(false)
    }
  }, [])

  /* ===== 인증 ===== */

  const loadSession = async () => {
    const me = await authApi.getMe()
    const contracts = await authApi.getMyContracts()
    const next = { ...me, contracts, contractId: contracts[0]?.id ?? null }
    save(next)
    await refresh(next).catch(() => {})
    return next
  }

  const logout = () => {
    setToken(null)
    save(null)
  }

  useEffect(() => {
    setUnauthorizedHandler(() => save(null))
  }, [])

  // 새로고침해도 로그인이 유지되도록 저장된 토큰으로 세션 복구
  useEffect(() => {
    if (!getToken()) return
    loadSession()
      .catch(() => {
        setToken(null)
        save(null)
      })
      .finally(() => setBooting(false))
  }, [])

  const login = async (phone, password) => {
    const { access_token } = await authApi.login(phone, password)
    setToken(access_token)
    return loadSession()
  }

  const signup = async (role, name, phone, password) => {
    const signupFn = role === 'LANDLORD' ? authApi.signupLandlord : authApi.signupTenant
    const { access_token } = await signupFn(name, phone, password)
    setToken(access_token)
    return loadSession()
  }

  const joinContract = async (code) => {
    await authApi.redeemInviteCode(code.trim().toUpperCase())
    return loadSession()
  }

  /* ===== 계약 등록 ===== */

  // 화면 하나가 건물 → 호실 → 계약 3단계 API로 나뉩니다. 같은 주소면 기존 건물을 재사용합니다.
  const addUnit = async (form) => {
    const buildings = await dataApi.getBuildings()
    const building =
      buildings.find((b) => b.address === form.address.trim()) ??
      (await dataApi.createBuilding({
        name: form.buildingName.trim() || null,
        address: form.address.trim(),
      }))

    const unit = await dataApi.createUnit(building.id, {
      dong: form.dong.trim(),
      ho: form.ho.trim(),
    })

    const contract = await dataApi.createContract(unit.id, {
      rent_amount: Number(form.rentAmount),
      maintenance_fee_fixed: Number(form.maintenanceFeeFixed),
      start_date: form.startDate,
      end_date: form.endDate,
    })

    const invite = await dataApi.issueInviteCode(unit.id, contract.id)
    await refresh()
    return { unitId: unit.id, contractId: contract.id, inviteCode: invite.code, expiresAt: invite.expires_at }
  }

  // 임차인이 아직 연결 안 된 세대의 초대코드를 새로 발급합니다(기존 코드를 읽는 API는 없음).
  const reissueInviteCode = async (unit) => {
    const invite = await dataApi.issueInviteCode(unit.unitId, unit.contractId)
    return invite.code
  }

  /* ===== 문제접수 ===== */

  // 사전합의 매칭 여부는 서버가 판단해서 agreement_matched / next_action으로 돌려줍니다.
  const addIssue = async ({ contractId, category, description, photoUrl }) => {
    const res = await dataApi.createIssue(contractId, { category, description, photo_url: photoUrl })
    await refresh()
    return {
      issueId: res.issue.id,
      status: res.issue.status,
      responsible: res.issue.responsible,
      matched: res.agreement_matched,
      note: res.agreement_note,
      nextAction: res.next_action,
    }
  }

  const resolveIssue = async (issue, { detail, cost, payer, receiptUrl }) => {
    await dataApi.resolveIssueApi(issue.contractId, issue.id, {
      resolver: 'LANDLORD',
      resolved_detail: detail,
      cost: Number(cost) || 0,
      payer,
      payment_status: 'PENDING',
      receipt_image_url: receiptUrl || null,
    })
    await refresh()
  }

  /* ===== 수리업체 · 사전합의 ===== */

  const saveVendors = async (list) => {
    await Promise.all(
      list.map((v) => dataApi.updateVendor(v.id, { category: v.category, name: v.name, phone: v.phone })),
    )
    await refresh()
  }

  const saveAgreements = async (list) => {
    await Promise.all(
      list.map((a) => dataApi.updateAgreement(a.contractId, a.id, { responsible: a.responsible, note: a.note })),
    )
    await refresh()
  }

  /* ===== 채팅 ===== */

  // 채팅방 목록 API가 없어서 계약 목록에서 만듭니다 (계약 1건 = 채팅방 1개).
  const rooms = data.units
    .filter((u) => u.contractId && u.tenantName)
    .map((u) => {
      const list = data.messages[u.contractId] || []
      const last = list[list.length - 1]
      return {
        id: u.contractId,
        contractId: u.contractId,
        counterpartName: user?.role === 'LANDLORD' ? `${u.tenantName} 임차인` : '임대인',
        unitLabel: dataApi.unitLabelOf(u),
        lastMessage: last?.content ?? '',
        lastAt: last?.sentAt ?? null,
      }
    })

  const sendMessage = async (contractId, text) => {
    const msg = await dataApi.postMessage(contractId, text)
    setData((prev) => ({
      ...prev,
      messages: {
        ...prev.messages,
        [contractId]: [
          ...(prev.messages[contractId] || []),
          {
            id: msg.id,
            type: msg.type,
            senderId: msg.sender_id,
            senderName: msg.sender_name,
            content: msg.content,
            refId: msg.ref_id,
            sentAt: msg.created_at,
          },
        ],
      },
    }))
  }

  const auth = { user, booting, login, signup, logout, joinContract }
  const value = {
    ...data,
    rooms,
    loading,
    refresh,
    addUnit,
    reissueInviteCode,
    addIssue,
    resolveIssue,
    saveVendors,
    saveAgreements,
    sendMessage,
  }

  return (
    <AuthContext.Provider value={auth}>
      <DataContext.Provider value={value}>{children}</DataContext.Provider>
    </AuthContext.Provider>
  )
}
