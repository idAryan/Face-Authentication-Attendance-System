"""Attendance database: punch-in and punch-out records."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DB_PATH


def get_connection(db_path: Optional[Path] = None):
    path = db_path or DB_PATH
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(path), timeout=10.0)


class AttendanceDB:
    """SQLite-backed attendance (punch-in / punch-out)."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self._init_schema()

    def _init_schema(self) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_attendance_user_id ON attendance(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(timestamp)"
            )
            conn.commit()

    def punch_in(self, user_id: str, name: str) -> bool:
        """Record punch-in. Returns True if recorded."""
        now = datetime.utcnow().isoformat() + "Z"
        with get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT INTO attendance (user_id, name, action, timestamp, created_at) VALUES (?, ?, 'punch_in', ?, ?)",
                (user_id, name, now, now),
            )
            conn.commit()
        return True

    def punch_out(self, user_id: str, name: str) -> bool:
        """Record punch-out."""
        now = datetime.utcnow().isoformat() + "Z"
        with get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT INTO attendance (user_id, name, action, timestamp, created_at) VALUES (?, ?, 'punch_out', ?, ?)",
                (user_id, name, now, now),
            )
            conn.commit()
        return True

    def get_records(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """Get attendance records, optionally filtered by user_id."""
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if user_id:
                cur = conn.execute(
                    "SELECT id, user_id, name, action, timestamp FROM attendance WHERE user_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (user_id, limit, offset),
                )
            else:
                cur = conn.execute(
                    "SELECT id, user_id, name, action, timestamp FROM attendance ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                    (limit, offset),
                )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_today_summary(self) -> List[dict]:
        """Get today's punch-in/out summary per user (last punch_in and last punch_out)."""
        with get_connection(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            today = datetime.utcnow().strftime("%Y-%m-%d")
            cur = conn.execute(
                """
                SELECT user_id, name,
                       MAX(CASE WHEN action = 'punch_in' THEN timestamp END) AS last_punch_in,
                       MAX(CASE WHEN action = 'punch_out' THEN timestamp END) AS last_punch_out
                FROM attendance
                WHERE date(timestamp) = date(?)
                GROUP BY user_id, name
                """,
                (today,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]
