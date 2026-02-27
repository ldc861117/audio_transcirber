"""
Task database module for Audio Transcriber.
Provides SQLite-backed storage for transcription tasks.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Database file path: data/tasks.db
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "tasks.db"


@contextmanager
def _get_db():
    """Yield a connection to the tasks database, ensuring it is always closed."""
    # Ensure data directory exists
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_task_db() -> None:
    """Create the transcriptions table if it does not exist."""
    with _get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transcriptions (
                id                 TEXT PRIMARY KEY,
                user_id            INTEGER NOT NULL,
                filename           TEXT NOT NULL,
                file_size_mb       REAL NOT NULL,
                transcript         TEXT DEFAULT '',
                status             TEXT DEFAULT 'queued',
                created_at         TIMESTAMP NOT NULL,
                updated_at         TIMESTAMP NOT NULL,
                enable_diarization BOOLEAN DEFAULT 0,
                speakers_json      TEXT DEFAULT '',
                error              TEXT DEFAULT '',
                provider           TEXT DEFAULT '',
                model              TEXT DEFAULT '',
                chunk_count        INTEGER DEFAULT 0,
                duration_seconds   REAL DEFAULT 0.0
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transcriptions_user
            ON transcriptions(user_id)
            """
        )
        conn.commit()
