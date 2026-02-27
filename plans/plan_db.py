import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "plans.db"

@contextmanager
def get_db_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_conn() as conn:
        # user_plans table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_plans (
                user_id          INTEGER PRIMARY KEY,
                tier             TEXT    NOT NULL DEFAULT 'free',
                monthly_minutes  INTEGER,
                used_minutes     REAL    DEFAULT 0.0,
                expires_at       TIMESTAMP,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # quota_usage table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quota_usage (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                task_id       TEXT    NOT NULL,
                minutes_used  REAL    NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trigger to update updated_at
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS update_user_plans_updated_at
            AFTER UPDATE ON user_plans
            FOR EACH ROW
            BEGIN
                UPDATE user_plans SET updated_at = CURRENT_TIMESTAMP WHERE user_id = OLD.user_id;
            END
        """)
        
        conn.commit()

# Initialize DB when module is imported
init_db()

def get_user_plan(user_id: int):
    with get_db_conn() as conn:
        return conn.execute("SELECT * FROM user_plans WHERE user_id = ?", (user_id,)).fetchone()

def upsert_user_plan(user_id: int, tier: str, monthly_minutes: int, expires_at=None):
    with get_db_conn() as conn:
        conn.execute("""
            INSERT INTO user_plans (user_id, tier, monthly_minutes, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                tier = excluded.tier,
                monthly_minutes = excluded.monthly_minutes,
                expires_at = excluded.expires_at,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, tier, monthly_minutes, expires_at))
        conn.commit()

def update_used_minutes(user_id: int, minutes: float):
    with get_db_conn() as conn:
        conn.execute("""
            UPDATE user_plans
            SET used_minutes = used_minutes + ?
            WHERE user_id = ?
        """, (minutes, user_id))
        conn.commit()

def add_quota_usage(user_id: int, task_id: str, minutes_used: float):
    with get_db_conn() as conn:
        conn.execute("""
            INSERT INTO quota_usage (user_id, task_id, minutes_used)
            VALUES (?, ?, ?)
        """, (user_id, task_id, minutes_used))
        conn.commit()

def get_quota_usage_history(user_id: int):
    with get_db_conn() as conn:
        return conn.execute("""
            SELECT * FROM quota_usage WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,)).fetchall()
