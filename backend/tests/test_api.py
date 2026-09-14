import os
os.environ['DATABASE_URL']='sqlite:///./test.db'
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.models import Machine
client=TestClient(app)
def setup_module(): Base.metadata.drop_all(engine); Base.metadata.create_all(engine); from app.main import bootstrap; bootstrap()
def token(): return client.post('/api/v1/auth/login',json={'login':'admin','password':'admin'}).json()['access_token']
def test_register_and_idempotent_sync():
 r=client.post('/api/v1/agent/register',json={'machine_uuid':'m-1','hostname':'PC-01'}); assert r.status_code==200 and r.json()['status']=='PENDING'
 machine_id=r.json()['machine_id']; approval=client.post(f'/api/v1/machines/{machine_id}/approve',headers={'Authorization':f'Bearer {token()}'}); agent=approval.json()['agent_token']
 payload={'activity_sessions':[{'event_uuid':'e-1','application':'EXCEL.EXE','started_at':'2026-01-01T10:00:00Z','ended_at':'2026-01-01T10:01:00Z','duration_seconds':60}]}
 headers={'Authorization':f'Bearer {agent}'}; assert client.post('/api/v1/agent/sync',json=payload,headers=headers).json()['accepted']==1
 assert client.post('/api/v1/agent/sync',json=payload,headers=headers).json()['accepted']==0
