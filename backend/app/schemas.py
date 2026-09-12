from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from .models import ContractStatus, Role


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
    address: str


class BuildingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
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
