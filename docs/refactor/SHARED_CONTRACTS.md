# Shared Contracts — V2 Migration Completion

> **ALL parallel Tracks MUST read and conform to these definitions.**
> NO Track should modify this file. Changes require cross-track consensus.

## 1. Database Convention

**Backend ORM: Flask-SQLAlchemy** (via `backend/db/base.py`)

All new models MUST:
- Inherit from `db.Model` (imported from `backend.db.base`)
- Use `datetime.now(timezone.utc)` instead of `datetime.utcnow()`
- Be imported in `backend/db/base.py` → `init_db()` to ensure table creation

```python
from datetime import datetime, timezone
from backend.db.base import db

class MyModel(db.Model):
    __tablename__ = 'my_table'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
```

## 2. TranscriptionTask Model Contract (Track A produces, Track C consumes)

Track A MUST create `backend/tasks/models.py` with this schema:

```python
class TranscriptionTask(db.Model):
    __tablename__ = 'transcriptions'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    file_size_mb = db.Column(db.Float, nullable=False)
    transcript = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='queued')
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    enable_diarization = db.Column(db.Boolean, default=False)
    speakers_json = db.Column(db.Text, default='')
    error = db.Column(db.Text, default='')
    provider = db.Column(db.String(100), default='')
    model = db.Column(db.String(100), default='')
    chunk_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Float, default=0.0)
```

Track A MUST create `backend/tasks/service.py` with this public API:

```python
class TaskService:
    @staticmethod
    def create_task(task_id, user_id, filename, file_size_mb, 
                    enable_diarization=False, provider='', model='') -> str: ...
    
    @staticmethod
    def update_task(task_id: str, **kwargs) -> bool: ...
    
    @staticmethod
    def get_task(task_id: str, user_id: int) -> Optional[dict]: ...
    
    @staticmethod
    def list_tasks(user_id: int, page=1, per_page=20, search='') -> dict: ...
    
    @staticmethod
    def delete_task(task_id: str, user_id: int) -> bool: ...
    
    @staticmethod
    def update_task_speakers(task_id: str, user_id: int, speaker_updates: list) -> bool: ...
```

Track C will update `backend/transcriptions/routes.py` to import:
```python
from backend.tasks.service import TaskService
```

## 3. SpeakerProfile & SpeakerClip Models (Track A produces)

Track A MUST rewrite `backend/speakers/db.py` to use SQLAlchemy, BUT:
- Keep ALL existing function signatures unchanged (e.g., `create_profile()`, `find_matching_profiles()`)
- `backend/speakers/service.py` (NOT in Track A's scope) must NOT need changes

## 4. Authentication Contract (Track B produces)

Track B MUST ensure `backend/auth/decorators.py` exports:
```python
from backend.auth.decorators import jwt_required, admin_required, subscription_required
```

Track B MUST create `backend/auth/desktop_adapter.py` exporting:
```python
def get_desktop_token(app) -> dict:
    """Auto-create/login local user, return {"access_token": str, "user": dict}"""
```

## 5. Error Response Contract (Track C produces)

Track C MUST create `backend/errors.py` with:
```python
def api_error(code: str, message: str, status: int = 400) -> tuple:
    """Returns (jsonify({"error": {"code": code, "message": message}}), status)"""
```

ALL API error responses across the project SHOULD use this format:
```json
{"error": {"code": "ERROR_CODE", "message": "Human readable message"}}
```

## 6. Directory Ownership (Exclusive Scope)

| Directory/File | Owner Track | Others: Read-Only |
|----------------|-------------|-------------------|
| `backend/tasks/` | Track A | Track C (consumer) |
| `backend/speakers/db.py` | Track A | - |
| `db/`, `models/`, `services/task_service.py` | Track A (DELETE) | - |
| `backend/auth/` | Track B | - |
| `backend/subscriptions/routes.py` | Track B (decorator fix only) | - |
| `auth.py` (root) | Track B | - |
| `backend/app.py` | Track C | - |
| `backend/config.py`, `backend/extensions.py` | Track C | - |
| `backend/errors.py` | Track C | - |
| `backend/transcriptions/` | Track C | - |
