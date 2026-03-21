"""
Task service for Audio Transcriber.
Business logic for managing transcription tasks in the database.

Consolidated from root services/task_service.py during Phase 3 cleanup.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.db.task_db import get_task_db, init_task_db
from .task_model import TranscriptionRecord

# Initialize the database table on import
init_task_db()


class TaskService:
    @staticmethod
    def create_task(
        task_id: str,
        user_id: int,
        filename: str,
        file_size_mb: float,
        enable_diarization: bool = False,
        provider: str = "",
        model: str = "",
    ) -> str:
        """Create a new transcription task in the database."""
        now = datetime.now().isoformat()
        with get_task_db() as conn:
            conn.execute(
                """
                INSERT INTO transcriptions (
                    id, user_id, filename, file_size_mb, status,
                    created_at, updated_at, enable_diarization,
                    provider, model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    user_id,
                    filename,
                    file_size_mb,
                    "queued",
                    now,
                    now,
                    1 if enable_diarization else 0,
                    provider,
                    model,
                ),
            )
            conn.commit()
        return task_id

    @staticmethod
    def update_task_speakers(task_id: str, user_id: int, speaker_updates: list) -> bool:
        """
        Update speaker labels/names for a task and synchronize the transcript.
        speaker_updates: list of {label: str, name: str, matched_profile_id: int|None}
        """
        task = TaskService.get_task(task_id, user_id)
        if not task:
            return False

        speakers = task.get("speakers", [])
        transcript = task.get("transcript", "")

        label_to_new_name = {}
        for update in speaker_updates:
            label = update.get("label")
            new_name = update.get("name")
            matched_id = update.get("matched_profile_id")
            if label:
                label_to_new_name[label] = {
                    "name": new_name,
                    "matched_profile_id": matched_id,
                }

        # 1. Update speakers metadata
        for spk in speakers:
            info = label_to_new_name.get(spk["label"])
            if info:
                spk["matched_name"] = info["name"]
                spk["matched_profile_id"] = info["matched_profile_id"]

        # 2. Synchronize transcript labels
        for label, info in label_to_new_name.items():
            new_name = info["name"]
            if not new_name or new_name == label:
                continue
            current_display = label
            for spk in task.get("speakers", []):
                if spk["label"] == label:
                    current_display = spk.get("matched_name") or spk["label"]
                    break
            if current_display != new_name:
                transcript = transcript.replace(f"【{current_display}】", f"【{new_name}】")
                transcript = transcript.replace(f"[{current_display}]", f"[{new_name}]")

        return TaskService.update_task(task_id, speakers=speakers, transcript=transcript)

    @staticmethod
    def update_task(task_id: str, **kwargs) -> bool:
        """Update an existing transcription task."""
        if not kwargs:
            return False

        kwargs["updated_at"] = datetime.now().isoformat()

        if "enable_diarization" in kwargs:
            kwargs["enable_diarization"] = 1 if kwargs["enable_diarization"] else 0
        if "speakers" in kwargs:
            kwargs["speakers_json"] = json.dumps(kwargs.pop("speakers"))

        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(task_id)

        with get_task_db() as conn:
            cursor = conn.execute(
                f"UPDATE transcriptions SET {fields} WHERE id = ?", tuple(values)
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_task(task_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific task for a user."""
        with get_task_db() as conn:
            row = conn.execute(
                "SELECT * FROM transcriptions WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            ).fetchone()
        if row:
            return TranscriptionRecord.from_db_row(row).to_dict()
        return None

    @staticmethod
    def list_tasks(
        user_id: int, page: int = 1, per_page: int = 20, search: str = ""
    ) -> Dict[str, Any]:
        """List tasks for a user with pagination and search."""
        offset = (page - 1) * per_page
        query = "SELECT * FROM transcriptions WHERE user_id = ?"
        params: List[Any] = [user_id]

        if search:
            query += " AND filename LIKE ?"
            params.append(f"%{search}%")

        count_query = query.replace("*", "COUNT(*)")

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        with get_task_db() as conn:
            total = conn.execute(count_query, tuple(params[:-2])).fetchone()[0]
            rows = conn.execute(query, tuple(params)).fetchall()

        items = [TranscriptionRecord.from_db_row(row).to_dict() for row in rows]
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    @staticmethod
    def delete_task(task_id: str, user_id: int) -> bool:
        """Delete a task for a user."""
        with get_task_db() as conn:
            cursor = conn.execute(
                "DELETE FROM transcriptions WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
