"""
User authentication module for Audio Transcriber.
Provides SQLite-backed user storage and Flask-Login integration.

DEPRECATION WARNING: This module is deprecated in favor of the V2 authentication
system in `backend/auth/`. It is maintained for legacy (V1) support only.
"""

import os
import warnings

warnings.warn(
    "The root `auth.py` is deprecated and will be removed in a future version. "
    "Please migrate to `backend.auth`.",
    DeprecationWarning,
    stacklevel=2
)
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask_login import LoginManager, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from app_paths import get_data_dir

# ── Database setup ─────────────────────────────────────────────
DB_DIR = get_data_dir()
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "users.db"


@contextmanager
def _get_db():
    """Yield a connection to the users database, ensuring it is always closed."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Create the users table if it does not exist."""
    with _get_db() as conn:
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


# ── User model ─────────────────────────────────────────────────
class User(UserMixin):
    """Minimal user object compatible with Flask-Login."""

    def __init__(self, user_id: int, username: str) -> None:
        self.id = user_id
        self.username = username

    @staticmethod
    def get_by_id(user_id: int) -> "User | None":
        with _get_db() as conn:
            row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            return User(row["id"], row["username"])
        return None

    @staticmethod
    def authenticate(username: str, password: str) -> "User | None":
        """Return a User if credentials are valid, else None."""
        with _get_db() as conn:
            row = conn.execute("SELECT id, username, password FROM users WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row["password"], password):
            return User(row["id"], row["username"])
        return None

    @staticmethod
    def create(username: str, password: str) -> "User":
        """Insert a new user and return the User object.

        Raises sqlite3.IntegrityError if the username already exists.
        """
        hashed = generate_password_hash(password)
        with _get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed),
            )
            conn.commit()
            user_id = cursor.lastrowid
        return User(user_id, username)

    @staticmethod
    def username_exists(username: str) -> bool:
        with _get_db() as conn:
            row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        return row is not None


# ── Flask-Login setup ──────────────────────────────────────────
login_manager = LoginManager()
login_manager.login_view = "login_page"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    try:
        return User.get_by_id(int(user_id))
    except (ValueError, TypeError):
        return None


def _persistent_secret_key() -> str:
    """Return a stable secret key, persisted to disk so sessions/JWTs survive restarts."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_file = Path(get_data_dir()) / ".secret_key"
    if key_file.exists():
        return key_file.read_text().strip()
    key = os.urandom(32).hex()
    key_file.write_text(key)
    return key


def get_or_create_local_user() -> "User":
    """Get or create the default 'local' user for desktop mode (no manual login needed)."""
    with _get_db() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE username = ?", ("local",)).fetchone()
    if row:
        return User(row["id"], row["username"])
    return User.create("local", os.urandom(16).hex())


def setup_auth(app) -> None:
    """Initialize auth: create DB tables and attach Flask-Login to the app."""
    app.secret_key = _persistent_secret_key()
    login_manager.init_app(app)
    init_db()

    @login_manager.unauthorized_handler
    def unauthorized():
        """Return 401 JSON for API requests, redirect for page requests."""
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith("/api/"):
            return jsonify({"error": "未登录，请先登录"}), 401
        return redirect(url_for("login_page"))
