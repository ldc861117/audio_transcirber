import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from ..db.base import db
from .models import Task

class TaskService:
    @staticmethod
    def create_task(task_id: str, user_id: int, filename: str, file_size_mb: float,
                    provider: str = "", model: str = "", enable_diarization: bool = False) -> Task:
        """Create a new transcription task."""
        task = Task(
            id=task_id,
            user_id=user_id,
            filename=filename,
            file_size_mb=file_size_mb,
            provider=provider,
            model=model,
            enable_diarization=enable_diarization,
            status="queued"
        )
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def update_task(task_id: str, user_id: int, **kwargs) -> bool:
        """Update a task's fields. Returns True if updated."""
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return False

        for key, value in kwargs.items():
            if hasattr(task, key):
                # Handle speakers_json specially if passed as a dict/list
                if key == "speakers" and (isinstance(value, list) or isinstance(value, dict)):
                    task.speakers_json = json.dumps(value)
                else:
                    setattr(task, key, value)

        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return True

    @staticmethod
    def get_task(task_id: str, user_id: int) -> Optional[Task]:
        """Get a single task by ID and user_id."""
        return Task.query.filter_by(id=task_id, user_id=user_id).first()

    @staticmethod
    def list_tasks(user_id: int, page: int = 1, per_page: int = 20, search: str = "") -> Dict[str, Any]:
        """List tasks for a user with pagination and optional search."""
        query = Task.query.filter_by(user_id=user_id)

        if search:
            query = query.filter(Task.filename.ilike(f"%{search}%"))

        pagination = query.order_by(Task.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages
        }

    @staticmethod
    def delete_task(task_id: str, user_id: int) -> bool:
        """Delete a task. Returns True if deleted."""
        task = Task.query.filter_by(id=task_id, user_id=user_id).first()
        if not task:
            return False

        db.session.delete(task)
        db.session.commit()
        return True
