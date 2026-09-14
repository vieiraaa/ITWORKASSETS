from datetime import datetime
from pydantic import BaseModel, Field

class RegisterRequest(BaseModel):
    machine_uuid: str; hostname: str; domain: str | None = None; current_user: str | None = None
    current_ip: str | None = None; os_version: str | None = None
class AgentSession(BaseModel):
    event_uuid: str; application: str; window_title: str | None = None; started_at: datetime; ended_at: datetime
    duration_seconds: int = Field(ge=0, le=86400); username: str | None = None
class IdleSessionIn(BaseModel):
    event_uuid: str; started_at: datetime; ended_at: datetime; duration_seconds: int = Field(ge=0, le=86400)
class SyncRequest(BaseModel):
    activity_sessions: list[AgentSession] = []; idle_sessions: list[IdleSessionIn] = []
class LoginRequest(BaseModel): login: str; password: str
class UserCreate(BaseModel): login: str; name: str; password: str; permissions: list[str] = []
class MachineUpdate(BaseModel):
    hostname: str | None = None
    domain: str | None = None
    current_user: str | None = None
    current_ip: str | None = None
    os_version: str | None = None
