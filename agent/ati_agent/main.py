import json, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import requests
from .storage import Storage
from .windows import foreground, idle_seconds, identity
def iso(): return datetime.now(timezone.utc).isoformat()
class Agent:
    def __init__(self, config):
        self.config=config; data=Path(config['data_directory']); data.mkdir(parents=True,exist_ok=True)
        self.store=Storage(data/'agent.db'); self.uuid=self.store.setting('machine_uuid') or str(uuid.uuid4()); self.store.save_setting('machine_uuid',self.uuid)
        self.token=self.store.setting('agent_token'); self.current=None; self.idle_start=None; self.last_sync=0; self.last_register=0
    @property
    def headers(self): return {'Authorization':f'Bearer {self.token}'} if self.token else {}
    def register(self):
        response=requests.post(f"{self.config['api_url']}/agent/register",json={'machine_uuid':self.uuid,**identity()},timeout=10); response.raise_for_status(); body=response.json()
        if body.get('agent_token'): self.token=body['agent_token']; self.store.save_setting('agent_token',self.token)
        self.last_register=time.time(); return body['status']
    def close_activity(self):
        if not self.current:return
        self.current['ended_at']=iso(); started=datetime.fromisoformat(self.current['started_at']); self.current['duration_seconds']=max(1,int((datetime.now(timezone.utc)-started).total_seconds()))
        self.store.add_activity(self.current); self.current=None
    def tick(self):
        now=iso(); is_idle=idle_seconds() >= self.config['idle_threshold_seconds']
        if not self.token and time.time()-self.last_register >= 60:
            try: self.register()
            except requests.RequestException: pass
        if is_idle:
            self.close_activity()
            if not self.idle_start:self.idle_start=now
        else:
            if self.idle_start:
                start=datetime.fromisoformat(self.idle_start); self.store.add_idle({'started_at':self.idle_start,'ended_at':now,'duration_seconds':max(1,int((datetime.now(timezone.utc)-start).total_seconds()))}); self.idle_start=None
            app,title=foreground(); signature=(app,title)
            if not self.current or (self.current['application'],self.current['window_title']) != signature:
                self.close_activity(); self.current={'application':app,'window_title':title,'started_at':now,'ended_at':now,'duration_seconds':0,'username':identity()['current_user']}
        if self.token and time.time()-self.last_sync >= self.config['sync_interval_seconds']:
            # Checkpoint ongoing state so the dashboard is current even without a window change.
            if self.current: self.close_activity()
            if self.idle_start:
                start=datetime.fromisoformat(self.idle_start); self.store.add_idle({'started_at':self.idle_start,'ended_at':now,'duration_seconds':max(1,int((datetime.now(timezone.utc)-start).total_seconds()))}); self.idle_start=now
            self.sync()
    def sync(self):
        try:
            requests.post(f"{self.config['api_url']}/agent/heartbeat",headers=self.headers,timeout=10).raise_for_status()
            payload=self.store.pending(); response=requests.post(f"{self.config['api_url']}/agent/sync",headers=self.headers,json=payload,timeout=30); response.raise_for_status(); self.store.mark_synced(payload)
            remote=requests.get(f"{self.config['api_url']}/agent/config",headers=self.headers,timeout=10).json()
            for key in ('collection_interval_seconds','sync_interval_seconds','idle_threshold_seconds'):
                if key in remote and isinstance(remote[key],int) and remote[key] > 0: self.config[key]=remote[key]
            self.last_sync=time.time()
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 401:
                self.token = None
                self.store.save_setting('agent_token', None)
                try: self.register()
                except requests.RequestException: pass
        except requests.RequestException: pass # queue remains intact for a later attempt
    def run(self, stop_event=None):
        status=self.register(); print(f"Machine {self.uuid}: {status}")
        while stop_event is None or not stop_event.is_set():
            self.tick()
            if stop_event is not None: stop_event.wait(self.config['collection_interval_seconds'])
            else: time.sleep(self.config['collection_interval_seconds'])
def main():
    config=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else 'config.json').read_text(encoding='utf-8')); Agent(config).run()
if __name__ == '__main__': main()
