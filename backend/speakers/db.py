"""
Speaker profile database module for Audio Transcriber.
Provides SQLite-backed storage for speaker voiceprint profiles and audio clips.
"""

import json
import sqlite3
import numpy as np
from contextlib import contextmanager
from typing import Optional
from app_paths import get_data_dir

# ── Database setup ─────────────────────────────────────────────
DB_DIR = get_data_dir()
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "speakers.db"

CLIPS_DIR = DB_DIR / "speaker_clips"
CLIPS_DIR.mkdir(exist_ok=True)


@contextmanager
def _get_db():
    """Yield a connection to the speakers database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_speaker_db() -> None:
    """Create speaker tables if they do not exist."""
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS speaker_profiles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                name        TEXT    NOT NULL DEFAULT '',
                embedding   BLOB   NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS speaker_clips (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id    INTEGER NOT NULL,
                clip_filename TEXT    NOT NULL,
                duration      REAL   NOT NULL DEFAULT 0.0,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (profile_id) REFERENCES speaker_profiles(id) ON DELETE CASCADE
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_profiles_user
            ON speaker_profiles(user_id)
        """)
        conn.commit()


# ── Embedding serialization ────────────────────────────────────

def _serialize_embedding(embedding: np.ndarray) -> bytes:
    """Convert a numpy embedding vector to bytes for SQLite storage."""
    return embedding.astype(np.float32).tobytes()


def _deserialize_embedding(blob: bytes) -> np.ndarray:
    """Convert bytes back to a numpy embedding vector."""
    return np.frombuffer(blob, dtype=np.float32)


# ── Profile CRUD ───────────────────────────────────────────────

def create_profile(user_id: int, embedding: np.ndarray, name: str = "") -> int:
    """Create a new speaker profile. Returns the profile ID."""
    with _get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO speaker_profiles (user_id, name, embedding) VALUES (?, ?, ?)",
            (user_id, name, _serialize_embedding(embedding)),
        )
        conn.commit()
        return cursor.lastrowid


def get_profile(profile_id: int) -> Optional[dict]:
    """Get a single speaker profile by ID."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT id, user_id, name, embedding, created_at, updated_at FROM speaker_profiles WHERE id = ?",
            (profile_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "embedding": _deserialize_embedding(row["embedding"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_profiles_for_user(user_id: int) -> list[dict]:
    """Get all speaker profiles for a given user."""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, user_id, name, embedding, created_at, updated_at "
            "FROM speaker_profiles WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    profiles = []
    for row in rows:
        profiles.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "embedding": _deserialize_embedding(row["embedding"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })
    return profiles


def update_profile_name(profile_id: int, name: str) -> bool:
    """Update a speaker profile's name. Returns True if updated."""
    with _get_db() as conn:
        cursor = conn.execute(
            "UPDATE speaker_profiles SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (name, profile_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_profile_embedding(profile_id: int, embedding: np.ndarray) -> bool:
    """Update a speaker profile's embedding (e.g. after averaging with new samples)."""
    with _get_db() as conn:
        cursor = conn.execute(
            "UPDATE speaker_profiles SET embedding = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (_serialize_embedding(embedding), profile_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_profile(profile_id: int) -> bool:
    """Delete a speaker profile and its clips. Returns True if deleted."""
    # Get clip files to remove from disk
    clips = get_clips_for_profile(profile_id)
    with _get_db() as conn:
        conn.execute("DELETE FROM speaker_clips WHERE profile_id = ?", (profile_id,))
        cursor = conn.execute("DELETE FROM speaker_profiles WHERE id = ?", (profile_id,))
        conn.commit()
    # Clean up clip files
    for clip in clips:
        clip_path = CLIPS_DIR / clip["clip_filename"]
        if clip_path.exists():
            clip_path.unlink()
    return cursor.rowcount > 0


def merge_profiles(keep_id: int, merge_id: int) -> bool:
    """Merge two profiles: move clips from merge_id to keep_id, average embeddings, delete merge_id."""
    profile_keep = get_profile(keep_id)
    profile_merge = get_profile(merge_id)
    if not profile_keep or not profile_merge:
        return False

    # Average embeddings
    avg_embedding = (profile_keep["embedding"] + profile_merge["embedding"]) / 2.0
    avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)  # Re-normalize

    with _get_db() as conn:
        # Move clips
        conn.execute(
            "UPDATE speaker_clips SET profile_id = ? WHERE profile_id = ?",
            (keep_id, merge_id),
        )
        # Update embedding
        conn.execute(
            "UPDATE speaker_profiles SET embedding = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (_serialize_embedding(avg_embedding), keep_id),
        )
        # Delete merged profile
        conn.execute("DELETE FROM speaker_profiles WHERE id = ?", (merge_id,))
        conn.commit()
    return True


# ── Clip CRUD ──────────────────────────────────────────────────

def add_clip(profile_id: int, clip_filename: str, duration: float) -> int:
    """Add a clip record. Returns the clip ID."""
    with _get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO speaker_clips (profile_id, clip_filename, duration) VALUES (?, ?, ?)",
            (profile_id, clip_filename, duration),
        )
        conn.commit()
        return cursor.lastrowid


def get_clips_for_profile(profile_id: int) -> list[dict]:
    """Get all clips for a speaker profile."""
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, profile_id, clip_filename, duration, created_at "
            "FROM speaker_clips WHERE profile_id = ? ORDER BY duration DESC",
            (profile_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "profile_id": row["profile_id"],
            "clip_filename": row["clip_filename"],
            "duration": row["duration"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def delete_clip(clip_id: int) -> bool:
    """Delete a clip record and its file."""
    with _get_db() as conn:
        row = conn.execute("SELECT clip_filename FROM speaker_clips WHERE id = ?", (clip_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM speaker_clips WHERE id = ?", (clip_id,))
        conn.commit()
    clip_path = CLIPS_DIR / row["clip_filename"]
    if clip_path.exists():
        clip_path.unlink()
    return True


# ── Similarity search ─────────────────────────────────────────

def find_matching_profiles(user_id: int, embedding: np.ndarray, threshold: float = 0.75) -> list[dict]:
    """
    Find stored profiles that match a given embedding above the threshold.
    Returns list of {profile_id, name, similarity} sorted by similarity desc.
    """
    profiles = get_profiles_for_user(user_id)
    matches = []
    emb_norm = embedding / np.linalg.norm(embedding)

    for p in profiles:
        stored_norm = p["embedding"] / np.linalg.norm(p["embedding"])
        similarity = float(np.dot(emb_norm, stored_norm))
        if similarity >= threshold:
            matches.append({
                "profile_id": p["id"],
                "name": p["name"],
                "similarity": round(similarity, 4),
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches


# Initialize on import
init_speaker_db()
