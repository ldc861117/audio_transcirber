from datetime import datetime, timezone
import json
from ..db.base import db

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_size_mb = db.Column(db.Float, nullable=False)
    transcript = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="queued")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    enable_diarization = db.Column(db.Boolean, default=False)
    speakers_json = db.Column(db.Text, default="")
    error = db.Column(db.Text, default="")
    provider = db.Column(db.String(50), default="")
    model = db.Column(db.String(50), default="")
    chunk_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Float, default=0.0)

    def to_dict(self):
        """Convert the record to a dictionary, suitable for API responses."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_size_mb": self.file_size_mb,
            "transcript": self.transcript,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "enable_diarization": self.enable_diarization,
            "error": self.error,
            "provider": self.provider,
            "model": self.model,
            "chunk_count": self.chunk_count,
            "duration_seconds": self.duration_seconds,
        }

        # Parse speakers_json if it's not empty
        if self.speakers_json:
            try:
                data["speakers"] = json.loads(self.speakers_json)
            except json.JSONDecodeError:
                data["speakers"] = []
        else:
            data["speakers"] = []

        return data
