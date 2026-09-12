import enum
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import (
    ChatMessageType,
    ContractStatus,
    CostBearer,
    IssueCategory,
    IssuePaymentStatus,
    IssueStatus,
    PaymentStatus,
    PaymentType,
    ResolutionActor,
    Responsible,
    Role,
)


class LandlordSignupRequest(BaseModel):
    name: str
    phone: str
    password: str = Field(min_length=8)


class TenantSignupRequest(BaseModel):
    name: str
    phone: str
    password: str = Field(min_length=8)


class RedeemInviteCodeRequest(BaseModel):
    invite_code: str


class LoginRequest(BaseModel):
    phone: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: Role
    name: str
    phone: str


class BuildingCreateRequest(BaseModel):
    name: str | None = None
    address: str


class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None = None
    address: str


class UnitCreateRequest(BaseModel):
    dong: str
    ho: str


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    building_id: str
    dong: str
    ho: str


class ContractCreateRequest(BaseModel):
    rent_amount: int
    maintenance_fee_fixed: int = 0
    start_date: date
    end_date: date


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    unit_id: str
    rent_amount: int
    maintenance_fee_fixed: int
    start_date: date
    end_date: date
    status: ContractStatus
    tenant_id: str | None = None


class InviteCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    contract_id: str
    expires_at: datetime


class ContractSummaryResponse(BaseModel):
    """지난 계약 목록 카드 하나에 해당 — '고려빌라 201호' 같은 표시용 요약."""

    id: str
    building_name: str
    dong: str
    ho: str
    start_date: date
    end_date: date
    status: ContractStatus


class ContractDetailResponse(BaseModel):
    id: str
    building_name: str
    address: str
    dong: str
    ho: str
    rent_amount: int
    maintenance_fee_fixed: int
    start_date: date
    end_date: date
    status: ContractStatus


class PaymentCreateRequest(BaseModel):
    type: PaymentType
    due_date: date
    amount: int


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: PaymentType
    due_date: date
    amount: int
    status: PaymentStatus
    paid_at: datetime | None = None


class IssueReportCreateRequest(BaseModel):
    category: IssueCategory
    description: str = Field(min_length=1)
    photo_url: str | None = None


class IssueReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contract_id: str
    category: IssueCategory
    description: str | None = None
    photo_url: str | None = None
    status: IssueStatus
    responsible: Responsible
    resolver: ResolutionActor | None = None
    resolved_detail: str | None = None
    cost: int | None = None
    payer: CostBearer | None = None
    payment_status: IssuePaymentStatus | None = None
    receipt_image_url: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class IssueCreateResponse(BaseModel):
    issue: IssueReportResponse
    agreement_matched: bool
    agreement_note: str | None = None
    next_action: str


class IssueResolveRequest(BaseModel):
    resolver: ResolutionActor
    resolved_detail: str = Field(min_length=1)
    cost: int = Field(ge=0)
    payer: CostBearer
    payment_status: IssuePaymentStatus
    receipt_image_url: str | None = None
    completed_at: datetime | None = None


class IssueStatusUpdateRequest(BaseModel):
    status: IssueStatus


class UploadResponse(BaseModel):
    url: str


class NotificationSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_alert: bool
    issue_alert: bool
    chat_alert: bool


class NotificationSettingsUpdateRequest(BaseModel):
    payment_alert: bool
    issue_alert: bool
    chat_alert: bool


class RepairVendorCreateRequest(BaseModel):
    category: IssueCategory
    name: str
    phone: str


class RepairVendorUpdateRequest(BaseModel):
    category: IssueCategory
    name: str
    phone: str


class RepairVendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    building_id: str
    category: IssueCategory
    name: str
    phone: str


class PriorAgreementCreateRequest(BaseModel):
    category: IssueCategory
    responsible: Responsible
    note: str | None = None


class PriorAgreementUpdateRequest(BaseModel):
    responsible: Responsible
    note: str | None = None


class PriorAgreementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contract_id: str
    category: IssueCategory
    responsible: Responsible
    note: str | None = None


class VendorAssignRequest(BaseModel):
    vendor_id: str | None = None


class BoardRowResponse(BaseModel):
    """건물·동·호수별 대시보드 한 줄. 계약이 없는(공실) 호실은 unit 정보만 채워진다."""

    unit_id: str
    dong: str
    ho: str
    contract_id: str | None = None
    tenant_name: str | None = None
    rent_amount: int | None = None
    maintenance_fee_fixed: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    payment_status: PaymentStatus | None = None
    assigned_vendor: RepairVendorResponse | None = None


class DuePaymentAlertResponse(BaseModel):
    """D-3/D-day/연체 알림 대상 1건. 실제 푸시 발송은 이 목록을 스케줄러가 폴링해서 연동."""

    payment_id: str
    contract_id: str
    building_name: str
    dong: str
    ho: str
    due_date: date
    amount: int
    type: PaymentType
    alert_type: str


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)


class ChatMessageResponse(BaseModel):
    id: str
    type: ChatMessageType
    sender_id: str | None = None
    sender_name: str | None = None
    content: str
    ref_id: str | None = None
    created_at: datetime


class DeviceTokenRegisterRequest(BaseModel):
    token: str = Field(min_length=1)
    platform: str | None = None


class DeviceTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    token: str
    platform: str | None = None
