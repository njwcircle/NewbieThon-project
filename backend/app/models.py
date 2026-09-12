import enum
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


def gen_invite_code() -> str:
    return uuid.uuid4().hex[:8].upper()


def default_invite_expiry() -> datetime:
    return datetime.utcnow() + timedelta(days=7)


class Role(str, enum.Enum):
    LANDLORD = "LANDLORD"
    TENANT = "TENANT"


class ContractStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    role = Column(SAEnum(Role), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Building(Base):
    __tablename__ = "buildings"

    id = Column(String, primary_key=True, default=gen_uuid)
    landlord_id = Column(String, ForeignKey("users.id"), nullable=False)
    address = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    units = relationship("Unit", back_populates="building")


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("building_id", "dong", "ho", name="uq_unit_location"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    dong = Column(String, nullable=False)
    ho = Column(String, nullable=False)

    building = relationship("Building", back_populates="units")
    contracts = relationship("Contract", back_populates="unit")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=gen_uuid)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    landlord_id = Column(String, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=True)
    rent_amount = Column(Integer, nullable=False)
    maintenance_fee_fixed = Column(Integer, nullable=False, default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SAEnum(ContractStatus), nullable=False, default=ContractStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("Unit", back_populates="contracts")


class InviteCode(Base):
    __tablename__ = "invite_codes"

    code = Column(String, primary_key=True, default=gen_invite_code)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    expires_at = Column(DateTime, default=default_invite_expiry)
    used_at = Column(DateTime, nullable=True)
