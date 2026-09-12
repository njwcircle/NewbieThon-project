from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import ContractStatus, IssueCategory, IssueStatus, PaymentStatus, PaymentType, Responsible, Role


class LandlordSignupRequest(BaseModel):
    name: str
    phone: str
    password: str = Field(min_length=8)


class TenantSignupRequest(BaseModel):
    invite_code: str
    name: str
    phone: str
    password: str = Field(min_length=8)


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


class IssueReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: IssueCategory
    description: str | None = None
    status: IssueStatus
    responsible: Responsible
    created_at: datetime
    resolved_at: datetime | None = None


class NotificationSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_alert: bool
    issue_alert: bool
    chat_alert: bool


class NotificationSettingsUpdateRequest(BaseModel):
    payment_alert: bool
    issue_alert: bool
    chat_alert: bool
