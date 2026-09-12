import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth, useData } from '../store'
import { formatWon, formatManwon, formatDate } from '../mock/constants'
import { agreementNote } from '../mock/units'
import HeroHeader from '../components/HeroHeader'
import ListCard from '../components/ListCard'
import StatusChip from '../components/StatusChip'
import BottomSheet from '../components/BottomSheet'
import SectionHeader from '../components/SectionHeader'
import InfoRow from '../components/InfoRow'
import Button from '../components/Button'
import EmptyState from '../components/EmptyState'

const unitMeta = (u) => {
  const room = u.dong ? `${u.dong} ${u.ho}호` : `${u.ho}호`
  if (u.state === 'VACANT') return `${room} · 계약 없음`
  if (u.state === 'PENDING') return `${room} · 임차인 미연결`
  return `${room} · ${u.tenantName} · 월 ${formatManwon(u.rentAmount)}`
}

export default function UnitsPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { units, vendors, agreements, setVendors, setAgreements } = useData()
  const [selectedId, setSelectedId] = useState(null)
  const [vendorDraft, setVendorDraft] = useState(null)
  const [termDraft, setTermDraft] = useState(null)

  const unit = units.find((u) => u.unitId === selectedId) || null
  if (user.role !== 'LANDLORD') return <Navigate to="/" replace />
  const myVendors = unit ? vendors.filter((v) => v.contractId === unit.contractId) : []
  const myTerms = unit ? agreements.filter((a) => a.contractId === unit.contractId) : []

  const close = () => {
    setSelectedId(null)
    setVendorDraft(null)
    setTermDraft(null)
  }

  const saveVendors = () => {
    setVendors((prev) => prev.map((v) => vendorDraft.find((d) => d.id === v.id) || v))
    setVendorDraft(null)
  }

  const saveTerms = () => {
    setAgreements((prev) => prev.map((a) => termDraft.find((d) => d.id === a.id) || a))
    setTermDraft(null)
  }

  return (
    <div className="page page--tabbed">
      <HeroHeader eyebrow={`총 ${units.length}세대 보유 중`} title="전체 세대" />

      <div className="units-bar">
        <span className="text-gray">최근 등록순 ▾</span>
        <button type="button" className="units-add" onClick={() => navigate('/contracts/new')}>
          ＋ 계약 추가
        </button>
      </div>

      <div className="page-body stack gap-12">
        {units.map((u) => (
          <ListCard
            key={u.unitId}
            title={u.buildingName}
            meta={unitMeta(u)}
            right={<StatusChip status={u.state} />}
            onClick={() => setSelectedId(u.unitId)}
          />
        ))}
      </div>

      <p className="caption text-center mt-24" style={{ paddingBottom: 24 }}>
        세대를 눌러 상세 정보를 확인하세요
      </p>

      <BottomSheet
        open={!!unit}
        onClose={close}
        title={unit?.buildingName}
        chip={unit && <StatusChip status={unit.state} />}
      >
        {unit && (
          <>
            <div className="sheet-section stack gap-16" style={{ paddingBottom: 24 }}>
              <InfoRow label="임차인" value={unit.tenantName || '-'} />
              <InfoRow label="연락처" value={unit.tenantPhone || '-'} />
              <InfoRow label="월세" value={formatWon(unit.rentAmount)} />
              <InfoRow label="관리비" value={formatWon(unit.maintenanceFeeFixed)} />
              <InfoRow
                label="계약 기간"
                value={
                  unit.startDate ? `${formatDate(unit.startDate)} ~ ${formatDate(unit.endDate)}` : '-'
                }
              />
              <InfoRow
                label="주소"
                value={`${unit.address}${unit.dong ? ` ${unit.dong}` : ''} ${unit.ho}호`}
              />
            </div>

            {unit.state === 'PENDING' && (
              <div className="sheet-section" style={{ paddingBottom: 8 }}>
                <div className="code-display">
                  <span className="contract-card-label">임차인 초대코드</span>
                  <span className="code-display-value">{unit.inviteCode}</span>
                  <span className="code-display-expire">발급일로부터 7일간 유효해요</span>
                </div>
              </div>
            )}

            <div className="sheet-divider mt-16" />

            {/* 수리업체 */}
            <div className="sheet-section">
              <SectionHeader
                title="수리업체"
                blue
                actionLabel={vendorDraft ? '취소' : '✏️ 수정'}
                onAction={() => setVendorDraft(vendorDraft ? null : myVendors.map((v) => ({ ...v })))}
              />

              {myVendors.length === 0 && !vendorDraft ? (
                <p className="caption">등록된 수리업체가 없어요</p>
              ) : (
                <div className="stack" style={{ gap: 10 }}>
                  {(vendorDraft || myVendors).map((v, i) => (
                    <div key={v.id} className="vendor-row">
                      <span className="vendor-category">{v.category}</span>
                      {vendorDraft ? (
                        <input
                          className="vendor-phone-input"
                          value={v.phone}
                          onChange={(e) => {
                            const next = [...vendorDraft]
                            next[i] = { ...v, phone: e.target.value }
                            setVendorDraft(next)
                          }}
                        />
                      ) : (
                        <span className="vendor-phone">{v.phone}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {vendorDraft && (
                <div className="edit-actions">
                  <Button small full onClick={saveVendors}>
                    저장
                  </Button>
                </div>
              )}
            </div>

            {/* 사전 협의내용 */}
            <div className="sheet-section">
              <SectionHeader
                title="사전 협의내용"
                blue
                actionLabel={termDraft ? '취소' : '✏️ 수정'}
                onAction={() => setTermDraft(termDraft ? null : myTerms.map((t) => ({ ...t })))}
              />

              {myTerms.length === 0 && !termDraft ? (
                <p className="caption">사전에 협의된 내용이 없어요</p>
              ) : (
                <div className="stack" style={{ gap: 10 }}>
                  {(termDraft || myTerms).map((t, i) => (
                    <div key={t.id} className="term-row">
                      <span>·</span>
                      {termDraft ? (
                        <input
                          className="term-input"
                          value={t.note}
                          onChange={(e) => {
                            const next = [...termDraft]
                            next[i] = { ...t, note: e.target.value }
                            setTermDraft(next)
                          }}
                        />
                      ) : (
                        <span>{t.note}</span>
                      )}
                    </div>
                  ))}
                  <p className="term-note">{agreementNote}</p>
                </div>
              )}

              {termDraft && (
                <div className="edit-actions">
                  <Button small full onClick={saveTerms}>
                    저장
                  </Button>
                </div>
              )}
            </div>
          </>
        )}
      </BottomSheet>

      {units.length === 0 && (
        <EmptyState icon="🏠" title="등록된 세대가 없어요" desc="계약을 등록하면 여기에 표시됩니다">
          <Button small onClick={() => navigate('/contracts/new')}>
            계약 등록하기
          </Button>
        </EmptyState>
      )}
    </div>
  )
}
