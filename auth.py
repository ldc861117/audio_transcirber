"""
User authentication module for Audio Transcriber.
Provides SQLite-backed user storage and Flask-Login integration.
"""

import os
import sqlite3
from pathlib import Path

from flask_login import LoginManager, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# ── Database setup ─────────────────────────────────────────────
DB_DIR = Path(__file__).resolve().parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "users.db"


def _get_db() -> sqlite3.Connection:
    """Return a connection to the users database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table if it does not exist."""
    conn = _get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


# ── User model ─────────────────────────────────────────────────
class User(UserMixin):
    """Minimal user object compatible with Flask-Login."""

    def __init__(self, user_id: int, username: str) -> None:
        self.id = user_id
        self.username = username

    @staticmethod
    def get_by_id(user_id: int) -> "User | None":
        conn = _get_db()
        row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if row:
            return User(row["id"], row["username"])
        return None

    @staticmethod
    def authenticate(username: str, password: str) -> "User | None":
        """Return a User if credentials are valid, else None."""
        conn = _get_db()
        row = conn.execute("SELECT id, username, password FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if row and check_password_hash(row["password"], password):
            return User(row["id"], row["username"])
        return None

    @staticmethod
    def create(username: str, password: str) -> "User":
        """Insert a new user and return the User object."""
        hashed = generate_password_hash(password)
        conn = _get_db()
        cursor = conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return User(user_id, username)

    @staticmethod
    def username_exists(username: str) -> bool:
        conn = _get_db()
        row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        return row is not None


# ── Flask-Login setup ──────────────────────────────────────────
login_manager = LoginManager()
login_manager.login_view = "login_page"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return User.get_by_id(int(user_id))


def setup_auth(app) -> None:
    """Initialize auth: create DB tables and attach Flask-Login to the app."""
    app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    login_manager.init_app(app)
    init_db()

    @login_manager.unauthorized_handler
    def unauthorized():
        """Return 401 JSON for API requests, redirect for page requests."""
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith("/api/"):
            return jsonify({"error": "未登录，请先登录"}), 401
        return redirect(url_for("login_page"))
