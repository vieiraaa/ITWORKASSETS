import json, sqlite3, uuid
from pathlib import Path
class Storage:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True); self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''CREATE TABLE IF NOT EXISTS configuration (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS activity_sessions (event_uuid TEXT PRIMARY KEY, application TEXT NOT NULL, window_title TEXT, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, duration_seconds INTEGER NOT NULL, username TEXT, synced INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS idle_sessions (event_uuid TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, duration_seconds INTEGER NOT NULL, synced INTEGER NOT NULL DEFAULT 0);'''); self.db.commit()
        for table in ('activity_sessions', 'idle_sessions'):
            columns = {row['name'] for row in self.db.execute(f'PRAGMA table_info({table})')}
            if 'synced' not in columns: self.db.execute(f'ALTER TABLE {table} ADD COLUMN synced INTEGER NOT NULL DEFAULT 0')
        self.db.commit()
    def setting(self, key, default=None):
        row=self.db.execute('SELECT value FROM configuration WHERE key=?',(key,)).fetchone(); return json.loads(row['value']) if row else default
    def save_setting(self,key,value): self.db.execute('INSERT OR REPLACE INTO configuration VALUES (?,?)',(key,json.dumps(value))); self.db.commit()
    def add_activity(self, item): self.db.execute('INSERT INTO activity_sessions (event_uuid, application, window_title, started_at, ended_at, duration_seconds, username, synced) VALUES (?,?,?,?,?,?,?,0)',(str(uuid.uuid4()),item['application'],item['window_title'],item['started_at'],item['ended_at'],item['duration_seconds'],item['username'])); self.db.commit()
    def add_idle(self,item): self.db.execute('INSERT INTO idle_sessions (event_uuid, started_at, ended_at, duration_seconds, synced) VALUES (?,?,?,?,0)',(str(uuid.uuid4()),item['started_at'],item['ended_at'],item['duration_seconds'])); self.db.commit()
    def pending(self):
        def rows(table): return [dict(r) for r in self.db.execute(f'SELECT * FROM {table} WHERE synced=0 ORDER BY started_at LIMIT 500')]
        return {'activity_sessions':rows('activity_sessions'),'idle_sessions':rows('idle_sessions')}
    def mark_synced(self, payload):
        for table, items in payload.items():
            if items:
                self.db.executemany(f'UPDATE {table} SET synced=1 WHERE event_uuid=?',[(x['event_uuid'],) for x in items])
        self.db.commit()
