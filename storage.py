"""Local SQLite state, outside the installation folder; no credentials in run records."""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

def data_dir():
    folder = Path(os.getenv("PAPER_LAB_DATA_DIR") or (Path(os.getenv("LOCALAPPDATA", Path.home() / ".local/share")) / "CryptoPaperLab"))
    folder.mkdir(parents=True, exist_ok=True)
    return folder

from contextlib import contextmanager

@contextmanager
def connect():
    db = sqlite3.connect(data_dir() / "lab.sqlite3", timeout=20)
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created TEXT NOT NULL, kind TEXT NOT NULL, params TEXT NOT NULL, payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS cache (id TEXT PRIMARY KEY, updated REAL NOT NULL, payload TEXT NOT NULL);
    """)
    try:
        with db:
            yield db
    finally:
        db.close()

def settings():
    with connect() as db:
        row = db.execute("SELECT payload FROM settings WHERE id=1").fetchone()
    return json.loads(row[0]) if row else {}

def save_settings(value):
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO settings VALUES(1,?)", (json.dumps(value, allow_nan=False),))
    return value

def save_run(kind, params, payload, run_id=None):
    run_id = run_id or uuid.uuid4().hex
    with connect() as db:
        db.execute("INSERT INTO runs VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                   (run_id, datetime.now(timezone.utc).isoformat(), kind, json.dumps(params, allow_nan=False), json.dumps(payload, allow_nan=False)))
    return run_id

def list_runs(limit=100):
    with connect() as db:
        rows = db.execute("SELECT id,created,kind,params FROM runs ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    return [dict(id=r[0], created=r[1], kind=r[2], params=json.loads(r[3])) for r in rows]

def get_run(run_id):
    with connect() as db:
        row = db.execute("SELECT id,created,kind,params,payload FROM runs WHERE id=?", (run_id,)).fetchone()
    if not row:
        raise KeyError(run_id)
    return dict(id=row[0], created=row[1], kind=row[2], params=json.loads(row[3]), payload=json.loads(row[4]))

def cache_get(key, ttl=300):
    import time
    with connect() as db:
        row = db.execute("SELECT updated,payload FROM cache WHERE id=?", (key,)).fetchone()
    return json.loads(row[1]) if row and time.time()-row[0] < ttl else None

def cache_put(key, payload):
    import time
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO cache VALUES(?,?,?)", (key, time.time(), json.dumps(payload, allow_nan=False)))
