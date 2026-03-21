"""
Task model for Audio Transcriber.
Defines the TranscriptionRecord dataclass for DB ↔ API serialization.

Consolidated from root models/task.py during Phase 3 cleanup.
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
import json
from typing import Optional, List, Any


@dataclass
class TranscriptionRecord:
    id: str
    user_id: int
    filename: str
    file_size_mb: float
    transcript: str = ""
    status: str = "queued"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    enable_diarization: bool = False
    speakers_json: str = ""
    error: str = ""
    provider: str = ""
    model: str = ""
    chunk_count: int = 0
    duration_seconds: float = 0.0

    @classmethod
    def from_db_row(cls, row: dict) -> "TranscriptionRecord":
        """Create a TranscriptionRecord from a SQLite row."""
        data = dict(row)
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["enable_diarization"] = bool(data.get("enable_diarization"))
        return cls(**data)

    def to_dict(self) -> dict:
        """Convert the record to a dictionary, suitable for API responses.

        Adds frontend-expected aliases:
        - task_id  → same as 'id'  (frontend reads task.task_id)
        - file_name → same as 'filename' (frontend reads task.file_name)
        """
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()

        # Frontend aliases
        d["task_id"] = d["id"]
        d["file_name"] = d["filename"]

        if self.speakers_json:
            try:
                d["speakers"] = json.loads(self.speakers_json)
            except json.JSONDecodeError:
                d["speakers"] = []
        else:
            d["speakers"] = []
        return d
