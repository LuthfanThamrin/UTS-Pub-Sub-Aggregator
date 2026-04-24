import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("data/dedup.db")


class DedupStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_events (
                topic        TEXT NOT NULL,
                event_id     TEXT NOT NULL,
                timestamp    TEXT NOT NULL,
                source       TEXT NOT NULL,
                payload      TEXT NOT NULL DEFAULT '{}',
                processed_at TEXT NOT NULL,
                PRIMARY KEY (topic, event_id)
            )
        """)
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_topic ON processed_events(topic)"
        )
        self.conn.commit()
        logger.info("DedupStore siap: %s", db_path)

    def is_duplicate(self, topic: str, event_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM processed_events WHERE topic=? AND event_id=? LIMIT 1",
            (topic, event_id),
        )
        return cur.fetchone() is not None

    def save(self, topic: str, event_id: str, timestamp: str,
             source: str, payload: dict, processed_at: str) -> bool:
        """
        Simpan event. Kembalikan True jika berhasil (baru),
        False jika sudah ada (duplikat). INSERT OR IGNORE bersifat atomis.
        """
        cur = self.conn.execute(
            """
            INSERT OR IGNORE INTO processed_events
                (topic, event_id, timestamp, source, payload, processed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (topic, event_id, timestamp, source, json.dumps(payload), processed_at),
        )
        self.conn.commit()
        if cur.rowcount == 0:
            logger.warning("[DUPLICATE DROPPED] topic=%s event_id=%s", topic, event_id)
            return False
        return True

    def get_by_topic(self, topic: str) -> list[dict]:
        cur = self.conn.execute(
            """
            SELECT topic, event_id, timestamp, source, payload, processed_at
            FROM processed_events
            WHERE topic = ?
            ORDER BY timestamp ASC, event_id ASC
            """,
            (topic,),
        )
        return [
            {
                "topic": r[0], "event_id": r[1], "timestamp": r[2],
                "source": r[3], "payload": json.loads(r[4]), "processed_at": r[5],
            }
            for r in cur.fetchall()
        ]

    def all_topics(self) -> list[str]:
        cur = self.conn.execute(
            "SELECT DISTINCT topic FROM processed_events ORDER BY topic"
        )
        return [r[0] for r in cur.fetchall()]

    def count_unique(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM processed_events")
        return cur.fetchone()[0]

    def close(self):
        self.conn.close()