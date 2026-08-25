"""Acumen Episodic Memory - SQLite + FTS5 task history."""

import json, sqlite3
from datetime import datetime
from acumen.core.config import EPISODIC_DB_PATH
from acumen.core.logger import get_logger

logger = get_logger("acumen.memory.episodic")

class EpisodicMemory:
    def __init__(self):
        self.db_path = str(EPISODIC_DB_PATH)
        self._init_db()

    def _connect(self): return sqlite3.connect(self.db_path)

    def _init_db(self):
        c = self._connect()
        c.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS episodes
            USING fts5(event_type, content, metadata, timestamp UNINDEXED);

            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT UNIQUE, root_cause TEXT,
                solution TEXT, times_seen INTEGER DEFAULT 1,
                last_seen TEXT DEFAULT (datetime('now'))
            );
        """)
        c.commit(); c.close()

    def save(self, event_type, content, metadata=None):
        c = self._connect()
        c.execute("INSERT INTO episodes VALUES (?,?,?,?)",
                  (event_type, content, json.dumps(metadata or {}),
                   datetime.now().isoformat()))
        c.commit(); c.close()

    def search(self, query, limit=5):
        c = self._connect()
        safe_query = ''.join(ch for ch in query if ch.isalnum() or ch == ' ')
        safe_query = safe_query.strip()
        if not safe_query:
            c.close()
            return []
        try:
            rows = c.execute(
                "SELECT event_type, content, metadata, timestamp "
                "FROM episodes WHERE episodes MATCH ? ORDER BY rank LIMIT ?",
                (safe_query, limit)).fetchall()
        except Exception:
            rows = []
        c.close()
        return [{"type":r[0],"content":r[1],"metadata":json.loads(r[2]),
                 "timestamp":r[3]} for r in rows]

    def save_error(self, sig, cause, solution):
        c = self._connect()
        c.execute("INSERT INTO error_patterns (error_signature,root_cause,solution) "
                  "VALUES (?,?,?) ON CONFLICT(error_signature) DO UPDATE SET "
                  "times_seen=times_seen+1, last_seen=datetime('now'), "
                  "root_cause=excluded.root_cause, solution=excluded.solution",
                  (sig, cause, solution))
        c.commit(); c.close()