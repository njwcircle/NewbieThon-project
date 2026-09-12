import { api, uploadFile } from './client'
import { CATEGORY } from '../constants'

/* ===== 엔드포인트 ===== */

export const getBuildings = () => api.get('/buildings')
export const createBuilding = (body) => api.post('/buildings', body)
export const createUnit = (buildingId, body) => api.post(`/buildings/${buildingId}/units`, body)
export const createContract = (unitId, body) => api.post(`/units/${unitId}/contracts`, body)
export const issueInviteCode = (unitId, contractId) =>
  api.post(`/units/${unitId}/contracts/${contractId}/invite-code`)

export const getBoard = (buildingId) => api.get(`/buildings/${buildingId}/board`)
export const getMyBoard = () => api.get('/users/me/board')

export const getVendors = (buildingId) => api.get(`/buildings/${buildingId}/repair-vendors`)
export const updateVendor = (vendorId, body) => api.patch(`/repair-vendors/${vendorId}`, body)

export const getAgreements = (contractId) => api.get(`/contracts/${contractId}/agreements`)
export const updateAgreement = (contractId, agreementId, body) =>
  api.patch(`/contracts/${contractId}/agreements/${agreementId}`, body)

export const getIssues = (contractId) => api.get(`/contracts/${contractId}/issues`)
export const createIssue = (contractId, body) => api.post(`/contracts/${contractId}/issues`, body)
export const resolveIssueApi = (contractId, issueId, body) =>
  api.post(`/contracts/${contractId}/issues/${issueId}/resolve`, body)

// 업로드는 인증 없이 호출 가능하고, 돌려받은 url을 photo_url/receipt_image_url에 그대로 넣습니다.
export const uploadIssueImage = (file) => uploadFile('/uploads/issues', file)
export const uploadReceiptImage = (file) => uploadFile('/uploads/receipts', file)

export const getMessages = (contractId) => api.get(`/contracts/${contractId}/messages`)
export const postMessage = (contractId, content) => api.post(`/contracts/${contractId}/messages`, { content })

/* ===== 응답 → 화면용 형태로 변환 ===== */

// "2층"처럼 이미 단위가 붙은 경우엔 '호'를 또 붙이지 않습니다.
const roomLabel = (dong, ho) => {
  const room = /[층호]$/.test(ho) ? ho : `${ho}호`
  return dong ? `${dong} ${room}` : room
}

export const unitLabelOf = (unit) => `${unit.buildingName} ${roomLabel(unit.dong, unit.ho)}`

// BoardRow + 건물 정보 → 대시보드 카드 한 줄
const toUnit = (building, row) => ({
  unitId: row.unit_id,
  contractId: row.contract_id,
  buildingId: building.id,
  buildingName: building.name || building.address,
  address: building.address,
  dong: row.dong || null,
  ho: row.ho,
  tenantName: row.tenant_name,
  rentAmount: row.rent_amount,
  maintenanceFeeFixed: row.maintenance_fee_fixed,
  startDate: row.start_date,
  endDate: row.end_date,
  paymentStatus: row.payment_status,
  assignedVendor: row.assigned_vendor,
})

// 백엔드엔 state 필드가 없어서 프론트에서 계산합니다.
const computeState = (unit, openIssues) => {
  if (!unit.contractId) return 'VACANT'
  if (!unit.tenantName) return 'PENDING'
  if (openIssues > 0) return 'ISSUE'
  return 'OCCUPIED'
}

// 백엔드 issue엔 title이 없어서 설명을 제목으로 씁니다.
const toIssue = (raw, unitLabel) => ({
  id: raw.id,
  contractId: raw.contract_id,
  unitLabel,
  category: raw.category,
  title: raw.description || `${CATEGORY[raw.category]} 문제`,
  description: raw.description,
  photoUrl: raw.photo_url,
  status: raw.status,
  responsible: raw.responsible,
  resolver: raw.resolver,
  resolvedDetail: raw.resolved_detail,
  cost: raw.cost,
  payer: raw.payer,
  paymentStatus: raw.payment_status,
  receiptImageUrl: raw.receipt_image_url,
  createdAt: raw.created_at?.slice(0, 10) ?? null,
  resolvedAt: raw.resolved_at?.slice(0, 10) ?? null,
})

export const toVendor = (raw) => ({
  id: raw.id,
  buildingId: raw.building_id,
  category: raw.category,
  name: raw.name,
  phone: raw.phone,
})

export const toAgreement = (raw) => ({
  id: raw.id,
  contractId: raw.contract_id,
  category: raw.category,
  responsible: raw.responsible,
  note: raw.note,
})

const toMessage = (raw) => ({
  id: raw.id,
  type: raw.type, // TEXT | SYSTEM_ISSUE | SYSTEM_PAYMENT
  senderId: raw.sender_id, // null이면 시스템 메시지
  senderName: raw.sender_name,
  content: raw.content,
  refId: raw.ref_id,
  sentAt: raw.created_at,
})

/* ===== 화면에 필요한 데이터를 한 번에 모아오기 ===== */

// 계약이 연결된 세대마다 문제·협의사항·메시지를 병렬로 받아옵니다.
async function loadPerContract(units) {
  const active = units.filter((u) => u.contractId)
  const [issueLists, agreementLists, messageLists] = await Promise.all([
    Promise.all(active.map((u) => getIssues(u.contractId).catch(() => []))),
    Promise.all(active.map((u) => getAgreements(u.contractId).catch(() => []))),
    Promise.all(active.map((u) => getMessages(u.contractId).catch(() => []))),
  ])

  const issues = []
  const agreements = []
  const messages = {}

  active.forEach((unit, i) => {
    const label = unitLabelOf(unit)
    issueLists[i].forEach((raw) => issues.push(toIssue(raw, label)))
    agreementLists[i].forEach((raw) => agreements.push(toAgreement(raw)))
    messages[unit.contractId] = messageLists[i].map(toMessage)
  })

  issues.sort((a, b) => (a.createdAt < b.createdAt ? 1 : -1))
  return { issues, agreements, messages }
}

const withState = (units, issues) =>
  units.map((u) => ({
    ...u,
    state: computeState(
      u,
      issues.filter((i) => i.contractId === u.contractId && i.status !== 'RESOLVED').length,
    ),
  }))

export async function loadLandlordData() {
  const buildings = await getBuildings()
  const boards = await Promise.all(buildings.map((b) => getBoard(b.id).catch(() => [])))

  const bare = []
  buildings.forEach((b, i) => boards[i].forEach((row) => bare.push(toUnit(b, row))))

  const { issues, agreements, messages } = await loadPerContract(bare)
  const vendorLists = await Promise.all(buildings.map((b) => getVendors(b.id).catch(() => [])))

  return {
    units: withState(bare, issues),
    issues,
    agreements,
    messages,
    vendors: vendorLists.flat().map(toVendor),
  }
}

export async function loadTenantData() {
  const rows = await getMyBoard()
  // 임차인에겐 건물 목록 API 권한이 없어서, 계약 상세에서 건물명/주소를 받아옵니다.
  const details = await Promise.all(rows.map((r) => api.get(`/contracts/${r.contract_id}`)))

  const bare = rows.map((row, i) =>
    toUnit({ id: null, name: details[i].building_name, address: details[i].address }, row),
  )

  const { issues, agreements, messages } = await loadPerContract(bare)
  return { units: withState(bare, issues), issues, agreements, messages, vendors: [] }
}

/* ===== 알림 설정 ===== */
export const getNotificationSettings = () => api.get('/users/me/notification-settings')
export const updateNotificationSettings = (body) => api.put('/users/me/notification-settings', body)
