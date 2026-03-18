# Track A: Database Layer Unification

## Goal
Migrate all sqlite3 direct-access database code to SQLAlchemy ORM, unifying the project onto a single database layer.

## Must Read Before Starting
- `docs/refactor/SHARED_CONTRACTS.md` — Model schemas and API contracts
- `backend/db/base.py` — Existing SQLAlchemy setup
- `services/task_service.py` — V1 TaskService to be replaced (understand existing API)
- `models/task.py` — V1 TranscriptionRecord dataclass (understand schema)
- `db/task_db.py` — V1 sqlite3 table schema
- `backend/speakers/db.py` — Speaker sqlite3 module to be migrated
- `backend/tests/conftest.py` — Existing test fixtures (use these patterns)

## Exclusive Scope (files you OWN)
- `backend/tasks/` — NEW module (create `__init__.py`, `models.py`, `service.py`)
- `backend/speakers/db.py` — REWRITE to SQLAlchemy
- `backend/db/base.py` — MODIFY (add new model imports)
- `db/task_db.py` — DELETE
- `models/task.py` — DELETE
- `services/task_service.py` — DELETE
- `speaker_db.py` (root) — DELETE
- `backend/tests/test_tasks.py` — NEW

## Do NOT Modify
- `backend/transcriptions/` (Track C owns)
- `backend/auth/` (Track B owns)
- `backend/speakers/service.py` (keep function call compatibility)

## Sub-tasks

### 1. Create `backend/tasks/__init__.py`
Empty init file to make it a package.

### 2. Create `backend/tasks/models.py`
SQLAlchemy model `TranscriptionTask` matching the schema in SHARED_CONTRACTS.md.
Must match the exact same columns as `db/task_db.py` CREATE TABLE schema.
Use `datetime.now(timezone.utc)` not `datetime.utcnow()`.
Include a `to_dict()` method that:
- Converts datetime to ISO format strings
- Parses `speakers_json` into a `speakers` list

### 3. Create `backend/tasks/service.py`
Port `services/task_service.py` logic to use SQLAlchemy.
Must preserve the EXACT same public API (method signatures in SHARED_CONTRACTS.md).
Key changes:
- Replace `_get_db()` context manager with `db.session`
- Replace raw SQL with SQLAlchemy queries
- Replace `conn.execute(f"UPDATE ... SET {fields}")` with model attribute assignment
- Keep `update_task_speakers()` logic intact (transcript label replacement)

### 4. Rewrite `backend/speakers/db.py`
Convert speaker_profiles and speaker_clips tables to SQLAlchemy models.
**CRITICAL**: Keep ALL existing function signatures unchanged:
- `create_profile(user_id, embedding, name)` → int
- `get_profile(profile_id)` → Optional[dict]
- `get_profiles_for_user(user_id)` → list[dict]
- `update_profile_name(profile_id, name)` → bool
- `update_profile_embedding(profile_id, embedding)` → bool
- `delete_profile(profile_id)` → bool
- `merge_profiles(keep_id, merge_id)` → bool
- `add_clip(profile_id, clip_filename, duration)` → int
- `get_clips_for_profile(profile_id)` → list[dict]
- `delete_clip(clip_id)` → bool
- `find_matching_profiles(user_id, embedding, threshold)` → list[dict]

The embedding serialization (numpy → bytes) still needs to work. Store as `db.Column(db.LargeBinary)`.
Keep `CLIPS_DIR` constant available for imports by `backend/speakers/service.py`.

### 5. Update `backend/db/base.py`
Add imports for new models:
```python
from backend.tasks.models import TranscriptionTask
from backend.speakers.db import SpeakerProfile, SpeakerClip
```

### 6. Delete old files
- `db/task_db.py`
- `models/task.py`
- `services/task_service.py`
- `speaker_db.py` (root)

### 7. Create `backend/tests/test_tasks.py`
Test the new TaskService with the existing conftest fixtures.
Test cases:
- create_task → get_task → verify fields
- update_task status/transcript
- list_tasks with pagination
- delete_task
- update_task_speakers (label replacement in transcript)

## Acceptance Criteria
```bash
python -m py_compile backend/tasks/models.py
python -m py_compile backend/tasks/service.py
python -m py_compile backend/speakers/db.py
python -c "from backend.tasks.models import TranscriptionTask"
python -c "from backend.tasks.service import TaskService"
python -c "from backend.speakers.db import create_profile, find_matching_profiles, CLIPS_DIR"
python -m pytest backend/tests/test_tasks.py -v
```

## Environment
- Python 3.13+, dependencies in requirements.txt
- If dependency install fails, skip tests, focus on syntax correctness
- Verification priority: `python -m py_compile` > import check > tests
