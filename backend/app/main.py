import secrets
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db, SessionLocal
from .models import User, UserPermission, Machine, ActivitySession, IdleSession, MetricSnapshot, AuditLog
from .schemas import RegisterRequest, SyncRequest, LoginRequest, UserCreate, MachineUpdate
from .security import hash_password, verify_password, create_token, require, current_user

app = FastAPI(title="ATI Work Analytics API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:9001"], allow_origin_regex=r"^https?://[^:]+:9001$", allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def audit(db, action, actor_id=None, details=None): db.add(AuditLog(action=action, actor_id=actor_id, details=details))
def bootstrap():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        permissions = ["dashboard.view", "machines.view", "machines.details", "activity.view", "idle.view", "users.view", "users.manage", "settings.view", "settings.manage", "applications.view"]
        if not db.scalar(select(User).where(User.login == "admin")):
            admin = User(login="admin", name="Administrator", password_hash=hash_password(settings.bootstrap_admin_password))
            admin.permissions = [UserPermission(permission=p) for p in permissions]
            db.add(admin); db.commit()
        if not db.scalar(select(User).where(User.login == "usuario")):
            user = User(login="usuario", name="Usuario ATI", password_hash=hash_password(settings.bootstrap_user_password))
            user.permissions = [UserPermission(permission=p) for p in permissions]
            db.add(user); db.commit()
@app.on_event("startup")
def startup(): bootstrap()
@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/api/v1/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.login == payload.login))
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
    audit(db, "auth.login", user.id); db.commit()
    return {"access_token": create_token(user), "token_type": "bearer", "user": {"name": user.name, "permissions": [p.permission for p in user.permissions]}}

@app.post("/api/v1/agent/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    machine = db.scalar(select(Machine).where(Machine.machine_uuid == payload.machine_uuid))
    if not machine:
        machine = Machine(**payload.model_dump(), status="PENDING")
        db.add(machine); audit(db, "machine.registration_requested", details=payload.hostname); db.commit(); db.refresh(machine)
    else:
        for key, value in payload.model_dump().items(): setattr(machine, key, value)
        db.commit()
    return {"machine_id": machine.id, "status": machine.status, "agent_token": machine.agent_token}

def agent_machine(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    token = authorization.removeprefix("Bearer ") if authorization else None
    machine = db.scalar(select(Machine).where(Machine.agent_token == token)) if token else None
    if not machine or machine.status not in {"APPROVED", "ONLINE"}: raise HTTPException(401, "Agent not approved")
    return machine
@app.post("/api/v1/agent/heartbeat")
def heartbeat(machine: Machine = Depends(agent_machine), db: Session = Depends(get_db)):
    machine.last_heartbeat_at = datetime.now(timezone.utc); machine.status = "ONLINE"; db.commit(); return {"ok": True}
@app.get("/api/v1/agent/config")
def agent_config(machine: Machine = Depends(agent_machine)):
    return {"collection_interval_seconds": 5, "sync_interval_seconds": 60, "idle_threshold_seconds": 60}
@app.post("/api/v1/agent/sync")
def sync(payload: SyncRequest, machine: Machine = Depends(agent_machine), db: Session = Depends(get_db)):
    inserted = 0
    for item in payload.activity_sessions:
        if not db.scalar(select(ActivitySession.id).where(ActivitySession.event_uuid == item.event_uuid)):
            db.add(ActivitySession(machine_id=machine.id, **item.model_dump())); inserted += 1
    for item in payload.idle_sessions:
        if not db.scalar(select(IdleSession.id).where(IdleSession.event_uuid == item.event_uuid)):
            db.add(IdleSession(machine_id=machine.id, **item.model_dump())); inserted += 1
    for item in payload.metric_snapshots:
        if not db.scalar(select(MetricSnapshot.id).where(MetricSnapshot.snapshot_uuid == item.snapshot_uuid)):
            db.add(MetricSnapshot(machine_id=machine.id, **item.model_dump())); inserted += 1
    machine.last_heartbeat_at = datetime.now(timezone.utc); machine.status = "ONLINE"; db.commit()
    return {"accepted": inserted}

@app.post("/api/v1/machines/{machine_id}/approve")
def approve_machine(machine_id: str, user: User = Depends(require("settings.manage")), db: Session = Depends(get_db)):
    machine = db.get(Machine, machine_id)
    if not machine: raise HTTPException(404, "Machine not found")
    machine.status = "APPROVED"; machine.agent_token = secrets.token_urlsafe(32); audit(db, "machine.approved", user.id, machine.hostname); db.commit()
    return {"machine_id": machine.id, "agent_token": machine.agent_token}

@app.get("/api/v1/machines")
def machines(user: User = Depends(require("machines.view")), db: Session = Depends(get_db)):
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.heartbeat_timeout_seconds)
    results=[]
    for m in db.scalars(select(Machine).order_by(Machine.hostname)).all():
        effective = "ONLINE" if m.last_heartbeat_at and m.last_heartbeat_at >= cutoff else ("PENDING" if m.status == "PENDING" else "OFFLINE")
        results.append({"id":m.id,"hostname":m.hostname,"user":m.current_user,"ip":m.current_ip,"status":effective,"last_heartbeat_at":m.last_heartbeat_at})
    return results
@app.get("/api/v1/machines/{machine_id}/activity")
def machine_activity(machine_id: str, application: str | None = Query(default=None), hours: int = Query(default=24, ge=1, le=720), user: User = Depends(require("activity.view")), db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = select(ActivitySession).where(ActivitySession.machine_id == machine_id, ActivitySession.ended_at >= since)
    if application: query = query.where(ActivitySession.application.ilike(f"%{application.strip()}%"))
    return db.scalars(query.order_by(ActivitySession.started_at.desc()).limit(2000)).all()

@app.get("/api/v1/machines/{machine_id}/telemetry")
def machine_telemetry(machine_id: str, hours: int = Query(default=24, ge=1, le=168), user: User = Depends(require("machines.details")), db: Session = Depends(get_db)):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    rows = db.scalars(select(MetricSnapshot).where(MetricSnapshot.machine_id == machine_id, MetricSnapshot.collected_at >= since).order_by(MetricSnapshot.collected_at.desc()).limit(1000)).all()
    latest = rows[0] if rows else None
    return {'latest': latest, 'history': list(reversed(rows))}
@app.get("/api/v1/machines/{machine_id}/analytics")
def machine_analytics(machine_id: str, application: str | None = Query(default=None), hours: int = Query(default=24, ge=1, le=720), user: User = Depends(require("activity.view")), db: Session = Depends(get_db)):
    machine = db.get(Machine, machine_id)
    if not machine: raise HTTPException(404, "Machine not found")
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = select(ActivitySession).where(ActivitySession.machine_id == machine_id, ActivitySession.ended_at >= since)
    if application: query = query.where(ActivitySession.application.ilike(f"%{application.strip()}%"))
    sessions = db.scalars(query).all()
    total = sum(item.duration_seconds for item in sessions)
    grouped = {}
    for item in sessions: grouped[item.application] = grouped.get(item.application, 0) + item.duration_seconds
    applications = [{"application": name, "seconds": seconds, "percentage": round(seconds * 100 / total, 1) if total else 0} for name, seconds in grouped.items()]
    applications.sort(key=lambda item: item["seconds"], reverse=True)
    timeline = []
    hour_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)
    for hour in range(24):
        start = hour_start + timedelta(hours=hour); end = start + timedelta(hours=1)
        seconds = sum(max(0, int((min(item.ended_at, end) - max(item.started_at, start)).total_seconds())) for item in sessions if item.started_at < end and item.ended_at > start)
        timeline.append({"start": start, "seconds": seconds, "is_work_hour": 7 <= start.astimezone(ZoneInfo("America/Sao_Paulo")).hour < 18})
    return {"applications": applications, "timeline": timeline, "total_seconds": total}
@app.patch("/api/v1/machines/{machine_id}")
def update_machine(machine_id: str, payload: MachineUpdate, user: User = Depends(require("machines.details")), db: Session = Depends(get_db)):
    machine = db.get(Machine, machine_id)
    if not machine: raise HTTPException(404, "Machine not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items(): setattr(machine, field, value)
    audit(db, "machine.updated", user.id, f"{machine.hostname}: {', '.join(changes)}")
    db.commit(); return {"id": machine.id, "updated": list(changes)}
@app.delete("/api/v1/machines/{machine_id}", status_code=204)
def delete_machine(machine_id: str, user: User = Depends(require("settings.manage")), db: Session = Depends(get_db)):
    machine = db.get(Machine, machine_id)
    if not machine: raise HTTPException(404, "Machine not found")
    hostname = machine.hostname
    db.query(ActivitySession).filter(ActivitySession.machine_id == machine_id).delete(synchronize_session=False)
    db.query(IdleSession).filter(IdleSession.machine_id == machine_id).delete(synchronize_session=False)
    db.query(MetricSnapshot).filter(MetricSnapshot.machine_id == machine_id).delete(synchronize_session=False)
    db.delete(machine); audit(db, "machine.deleted", user.id, hostname); db.commit()
@app.get("/api/v1/dashboard/overview")
def overview(user: User = Depends(require("dashboard.view")), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Machine)) or 0
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.heartbeat_timeout_seconds)
    online = db.scalar(select(func.count()).select_from(Machine).where(Machine.last_heartbeat_at >= cutoff)) or 0
    since = datetime.now(timezone.utc) - timedelta(days=1)
    active = db.scalar(select(func.coalesce(func.sum(ActivitySession.duration_seconds),0)).where(ActivitySession.started_at >= since)) or 0
    idle = db.scalar(select(func.coalesce(func.sum(IdleSession.duration_seconds),0)).where(IdleSession.started_at >= since)) or 0
    apps = db.execute(select(ActivitySession.application, func.sum(ActivitySession.duration_seconds).label("seconds")).where(ActivitySession.started_at >= since).group_by(ActivitySession.application).order_by(func.sum(ActivitySession.duration_seconds).desc()).limit(5)).all()
    return {"machines_total":total,"online":online,"offline":total-online,"active_seconds":active,"idle_seconds":idle,"top_applications":[{"application":a,"seconds":s} for a,s in apps]}

@app.get("/api/v1/users")
def users(user: User = Depends(require("users.view")), db: Session = Depends(get_db)):
    return [{"id":u.id,"login":u.login,"name":u.name,"active":u.is_active,"permissions":[p.permission for p in u.permissions]} for u in db.scalars(select(User)).all()]
@app.post("/api/v1/users")
def create_user(payload: UserCreate, user: User = Depends(require("users.manage")), db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.login == payload.login)): raise HTTPException(409, "Login already exists")
    new = User(login=payload.login, name=payload.name, password_hash=hash_password(payload.password)); new.permissions=[UserPermission(permission=p) for p in payload.permissions]
    db.add(new); audit(db,"user.created",user.id,payload.login); db.commit(); return {"id":new.id}
