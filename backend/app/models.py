import enum
import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    JSON,
    text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

# --- ENUMS ---
class AppNameEnum(str, enum.Enum):
    RAPID_CAT = "RAPID_CAT"
    RISING_TIDE = "RISING_TIDE"
    MATERIAL_INTEL = "MATERIAL_INTEL"
    NETWORK_PLATFORM = "NETWORK_PLATFORM"

class SubscriptionStatusEnum(str, enum.Enum):
    active = "active"
    trialing = "trialing"
    past_due = "past_due"
    canceled = "canceled"
    incomplete = "incomplete"

class EventStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

# --- PLACEHOLDER MODELS ---
# These models are external dependencies where we do not own the schema definition,
# but we need to reference them or write to them.

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True)
    subdomain = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True) # Shop Name
    # Placeholder for other columns
    # Placeholder for other columns

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=True)
    # Placeholder for other columns

class TenantMembership(Base):
    __tablename__ = "tenant_memberships"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String, default="Owner")

class TenantAppAccess(Base):
    __tablename__ = "tenant_app_access"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.id"))
    app_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # Placeholder for other columns

class UserPlatformAccess(Base):
    __tablename__ = "user_platform_access"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    # Placeholder for other columns


# --- CORE MODELS ---

class PlatformPlan(Base):
    __tablename__ = "platform_plans"

    id = Column(Integer, primary_key=True)
    stripe_price_id = Column(String, nullable=False)
    app_name = Column(Enum(AppNameEnum), nullable=False)
    plan_tier = Column(String, nullable=False)
    is_trial = Column(Boolean, default=False)
    trial_days = Column(Integer, default=0)
    features_config = Column(JSON, default={})


class StripeCustomer(Base):
    __tablename__ = "stripe_customers"

    id = Column(Integer, primary_key=True)
    stripe_customer_id = Column(String, unique=True, nullable=False)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    billing_email = Column(String, nullable=True)
    payment_method_id = Column(String, nullable=True)
    
    # Relationships (optional but helpful)
    tenant = relationship("Tenant")
    user = relationship("User")


class PlatformSubscription(Base):
    __tablename__ = "platform_subscriptions"

    id = Column(Integer, primary_key=True)
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    stripe_customer_id = Column(Integer, ForeignKey("stripe_customers.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("platform_plans.id"), nullable=False)
    status = Column(Enum(SubscriptionStatusEnum), nullable=False)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("StripeCustomer")
    plan = relationship("PlatformPlan")


class StripeEvent(Base):
    __tablename__ = "stripe_events"

    stripe_event_id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    status = Column(Enum(EventStatusEnum), default=EventStatusEnum.PENDING)
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
