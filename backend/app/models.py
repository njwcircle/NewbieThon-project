import enum
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
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


class PaymentType(str, enum.Enum):
    RENT = "RENT"
    MAINTENANCE_FIXED = "MAINTENANCE_FIXED"
    MAINTENANCE_VARIABLE = "MAINTENANCE_VARIABLE"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class IssueCategory(str, enum.Enum):
    BOILER = "BOILER"
    WATER = "WATER"
    ELECTRIC = "ELECTRIC"
    WALL = "WALL"
    FURNITURE = "FURNITURE"
    ETC = "ETC"


class Responsible(str, enum.Enum):
    LANDLORD = "LANDLORD"
    TENANT = "TENANT"
    UNDEFINED = "UNDEFINED"


class IssueStatus(str, enum.Enum):
    RECEIVED = "RECEIVED"
    AUTO_RESOLVED = "AUTO_RESOLVED"
    IN_CHAT = "IN_CHAT"
    RESOLVED = "RESOLVED"


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
    name = Column(String, nullable=True)
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


class RepairVendor(Base):
    __tablename__ = "repair_vendors"

    id = Column(String, primary_key=True, default=gen_uuid)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    category = Column(SAEnum(IssueCategory), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=gen_uuid)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    landlord_id = Column(String, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("users.id"), nullable=True)
    assigned_vendor_id = Column(String, ForeignKey("repair_vendors.id"), nullable=True)
    rent_amount = Column(Integer, nullable=False)
    maintenance_fee_fixed = Column(Integer, nullable=False, default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(SAEnum(ContractStatus), nullable=False, default=ContractStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

    unit = relationship("Unit", back_populates="contracts")
    tenant = relationship("User", foreign_keys=[tenant_id])
    assigned_vendor = relationship("RepairVendor")
    payments = relationship("Payment", backref="contract")


class PriorAgreement(Base):
    __tablename__ = "prior_agreements"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    category = Column(SAEnum(IssueCategory), nullable=False)
    responsible = Column(SAEnum(Responsible), nullable=False)
    note = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InviteCode(Base):
    __tablename__ = "invite_codes"

    code = Column(String, primary_key=True, default=gen_invite_code)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    expires_at = Column(DateTime, default=default_invite_expiry)
    used_at = Column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    type = Column(SAEnum(PaymentType), nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    proof_image_url = Column(String, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IssueReport(Base):
    __tablename__ = "issue_reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False)
    category = Column(SAEnum(IssueCategory), nullable=False)
    description = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    status = Column(SAEnum(IssueStatus), nullable=False, default=IssueStatus.RECEIVED)
    responsible = Column(SAEnum(Responsible), nullable=False, default=Responsible.UNDEFINED)
    resolved_detail = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    payment_alert = Column(Boolean, nullable=False, default=True)
    issue_alert = Column(Boolean, nullable=False, default=True)
    chat_alert = Column(Boolean, nullable=False, default=True)
