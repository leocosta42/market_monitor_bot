"""
Deduplicacao PERSISTENTE de alertas.

Antes o controle era um dict em memoria: reiniciava o bot -> reenviava tudo,
e o dict crescia para sempre. Aqui usamos SQLite, com limpeza de entradas antigas.
"""
import os
import time
import sqlite3
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class DedupStore:
    def __init__(self, db_path: str, ttl_hours: int = 12):
        self.db_path = db_path
        self.ttl_seconds = ttl_hours * 3600
        self._lock = Lock()
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS alerts (match_id TEXT PRIMARY KEY, sent_at REAL)"
        )
        self._conn.commit()

    def already_alerted(self, match_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "SELECT 1 FROM alerts WHERE match_id = ?", (str(match_id),)
            )
            return cur.fetchone() is not None

    def mark(self, match_id: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO alerts (match_id, sent_at) VALUES (?, ?)",
                (str(match_id), time.time()),
            )
            self._conn.commit()

    def cleanup(self) -> int:
        """Remove alertas mais antigos que o TTL (jogos ja encerrados)."""
        cutoff = time.time() - self.ttl_seconds
        with self._lock:
            cur = self._conn.execute("DELETE FROM alerts WHERE sent_at < ?", (cutoff,))
            self._conn.commit()
            return cur.rowcount

    def close(self) -> None:
        with self._lock:
            self._conn.close()
