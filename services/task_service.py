"""
Task service module for Audio Transcriber.
Provides business logic for managing transcription tasks.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from db.task_db import _get_db, init_task_db
from models.task import TranscriptionRecord

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
        with _get_db() as conn:
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
    def update_task(task_id: str, **kwargs) -> bool:
        """Update an existing transcription task."""
        if not kwargs:
            return False

        kwargs["updated_at"] = datetime.now().isoformat()

        # Handle special field conversions
        if "enable_diarization" in kwargs:
            kwargs["enable_diarization"] = 1 if kwargs["enable_diarization"] else 0
        if "speakers" in kwargs:
            kwargs["speakers_json"] = json.dumps(kwargs.pop("speakers"))

        fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(task_id)

        with _get_db() as conn:
            cursor = conn.execute(
                f"UPDATE transcriptions SET {fields} WHERE id = ?", tuple(values)
            )
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def get_task(task_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific task for a user."""
        with _get_db() as conn:
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

        with _get_db() as conn:
            total = conn.execute(count_query, tuple(params[:-2])).fetchone()[0]
            rows = conn.execute(query, tuple(params)).fetchall()

        items = [TranscriptionRecord.from_db_row(row).to_dict() for row in rows]
        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }

    @staticmethod
    def delete_task(task_id: str, user_id: int) -> bool:
        """Delete a task for a user."""
        with _get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM transcriptions WHERE id = ? AND user_id = ?",
                (task_id, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
