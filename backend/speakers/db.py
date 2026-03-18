"""
Speaker profile database module for Audio Transcriber.
Provides SQLAlchemy-backed storage for speaker voiceprint profiles and audio clips.
"""

import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from ..db.base import db
from app_paths import get_data_dir

# ── Setup ─────────────────────────────────────────────
DB_DIR = get_data_dir()
CLIPS_DIR = DB_DIR / "speaker_clips"
CLIPS_DIR.mkdir(exist_ok=True, parents=True)

# ── Models ─────────────────────────────────────────────

class SpeakerProfile(db.Model):
    __tablename__ = 'speaker_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, default='')
    embedding = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    clips = db.relationship('SpeakerClip', backref='profile', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "embedding": _deserialize_embedding(self.embedding).tolist(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class SpeakerClip(db.Model):
    __tablename__ = 'speaker_clips'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('speaker_profiles.id', ondelete='CASCADE'), nullable=False)
    clip_filename = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "clip_filename": self.clip_filename,
            "duration": self.duration,
            "created_at": self.created_at.isoformat(),
        }

# ── Embedding serialization ────────────────────────────────────

def _serialize_embedding(embedding: np.ndarray) -> bytes:
    """Convert a numpy embedding vector to bytes for database storage."""
    return embedding.astype(np.float32).tobytes()


def _deserialize_embedding(blob: bytes) -> np.ndarray:
    """Convert bytes back to a numpy embedding vector."""
    return np.frombuffer(blob, dtype=np.float32)


# ── Profile CRUD ───────────────────────────────────────────────

def create_profile(user_id: int, embedding: np.ndarray, name: str = "") -> int:
    """Create a new speaker profile. Returns the profile ID."""
    profile = SpeakerProfile(
        user_id=user_id,
        name=name,
        embedding=_serialize_embedding(embedding)
    )
    db.session.add(profile)
    db.session.commit()
    return profile.id


def get_profile(profile_id: int) -> Optional[Dict[str, Any]]:
    """Get a single speaker profile by ID."""
    profile = db.session.get(SpeakerProfile, profile_id)
    if not profile:
        return None
    # Use internal dict conversion if called from other python code expecting numpy
    res = profile.to_dict()
    res["embedding"] = np.array(res["embedding"], dtype=np.float32)
    return res


def get_profiles_for_user(user_id: int) -> List[Dict[str, Any]]:
    """Get all speaker profiles for a given user."""
    profiles = SpeakerProfile.query.filter_by(user_id=user_id).order_by(SpeakerProfile.updated_at.desc()).all()
    res_list = []
    for p in profiles:
        d = p.to_dict()
        d["embedding"] = np.array(d["embedding"], dtype=np.float32)
        res_list.append(d)
    return res_list


def update_profile_name(profile_id: int, name: str) -> bool:
    """Update a speaker profile's name. Returns True if updated."""
    profile = db.session.get(SpeakerProfile, profile_id)
    if not profile:
        return False
    profile.name = name
    db.session.commit()
    return True


def update_profile_embedding(profile_id: int, embedding: np.ndarray) -> bool:
    """Update a speaker profile's embedding (e.g. after averaging with new samples)."""
    profile = db.session.get(SpeakerProfile, profile_id)
    if not profile:
        return False
    profile.embedding = _serialize_embedding(embedding)
    db.session.commit()
    return True


def delete_profile(profile_id: int) -> bool:
    """Delete a speaker profile and its clips. Returns True if deleted."""
    profile = db.session.get(SpeakerProfile, profile_id)
    if not profile:
        return False

    # Get clip files to remove from disk
    clips = SpeakerClip.query.filter_by(profile_id=profile_id).all()
    clip_filenames = [c.clip_filename for c in clips]

    db.session.delete(profile)
    db.session.commit()

    # Clean up clip files
    for filename in clip_filenames:
        clip_path = CLIPS_DIR / filename
        if clip_path.exists():
            clip_path.unlink()
    return True


def merge_profiles(keep_id: int, merge_id: int) -> bool:
    """Merge two profiles: move clips from merge_id to keep_id, average embeddings, delete merge_id."""
    profile_keep = db.session.get(SpeakerProfile, keep_id)
    profile_merge = db.session.get(SpeakerProfile, merge_id)
    if not profile_keep or not profile_merge:
        return False

    # Average embeddings
    emb_keep = _deserialize_embedding(profile_keep.embedding)
    emb_merge = _deserialize_embedding(profile_merge.embedding)

    avg_embedding = (emb_keep + emb_merge) / 2.0
    avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)  # Re-normalize

    # Move clips
    SpeakerClip.query.filter_by(profile_id=merge_id).update({"profile_id": keep_id})

    # Update keep profile
    profile_keep.embedding = _serialize_embedding(avg_embedding)

    # Delete merged profile
    db.session.delete(profile_merge)
    db.session.commit()
    return True


# ── Clip CRUD ──────────────────────────────────────────────────

def add_clip(profile_id: int, clip_filename: str, duration: float) -> int:
    """Add a clip record. Returns the clip ID."""
    clip = SpeakerClip(
        profile_id=profile_id,
        clip_filename=clip_filename,
        duration=duration
    )
    db.session.add(clip)
    db.session.commit()
    return clip.id


def get_clips_for_profile(profile_id: int) -> List[Dict[str, Any]]:
    """Get all clips for a speaker profile."""
    clips = SpeakerClip.query.filter_by(profile_id=profile_id).order_by(SpeakerClip.duration.desc()).all()
    return [c.to_dict() for c in clips]


def delete_clip(clip_id: int) -> bool:
    """Delete a clip record and its file."""
    clip = db.session.get(SpeakerClip, clip_id)
    if not clip:
        return False

    filename = clip.clip_filename
    db.session.delete(clip)
    db.session.commit()

    clip_path = CLIPS_DIR / filename
    if clip_path.exists():
        clip_path.unlink()
    return True


# ── Similarity search ─────────────────────────────────────────

def find_matching_profiles(user_id: int, embedding: np.ndarray, threshold: float = 0.75) -> List[Dict[str, Any]]:
    """
    Find stored profiles that match a given embedding above the threshold.
    Returns list of {profile_id, name, similarity} sorted by similarity desc.
    """
    profiles = SpeakerProfile.query.filter_by(user_id=user_id).all()
    matches = []
    emb_norm = embedding / np.linalg.norm(embedding)

    for p in profiles:
        stored_emb = _deserialize_embedding(p.embedding)
        stored_norm = stored_emb / np.linalg.norm(stored_emb)
        similarity = float(np.dot(emb_norm, stored_norm))
        if similarity >= threshold:
            matches.append({
                "profile_id": p.id,
                "name": p.name,
                "similarity": round(similarity, 4),
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches
