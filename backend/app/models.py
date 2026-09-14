import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now(): return datetime.now(timezone.utc)
def uid(): return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    login: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    permissions: Mapped[list["UserPermission"]] = relationship(cascade="all, delete-orphan")

class UserPermission(Base):
    __tablename__ = "user_permissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    permission: Mapped[str] = mapped_column(String(100), index=True)

class Machine(Base):
    __tablename__ = "machines"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    machine_uuid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    os_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    agent_token: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

class ActivitySession(Base):
    __tablename__ = "activity_sessions"
    __table_args__ = (UniqueConstraint("event_uuid", name="uq_activity_event"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    event_uuid: Mapped[str] = mapped_column(String(36), index=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    application: Mapped[str] = mapped_column(String(255), index=True)
    window_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)

class IdleSession(Base):
    __tablename__ = "idle_sessions"
    __table_args__ = (UniqueConstraint("event_uuid", name="uq_idle_event"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    event_uuid: Mapped[str] = mapped_column(String(36), index=True)
    machine_id: Mapped[str] = mapped_column(ForeignKey("machines.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
