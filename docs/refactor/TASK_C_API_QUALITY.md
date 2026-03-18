# Track C: API Quality & Error Handling

## Goal
Unify error response format, replace print() with Python logging, tighten CORS, and update imports to consume Track A's new TaskService.

## Must Read Before Starting
- `docs/refactor/SHARED_CONTRACTS.md` — Error response format and TaskService API
- `backend/app.py` — V2 application factory
- `backend/config.py` — Configuration classes
- `backend/extensions.py` — CORS setup
- `backend/transcriptions/routes.py` — Main transcription API routes (has print and old imports)
- `backend/transcriptions/service.py` — Core transcription service (many print statements)
- `backend/tests/conftest.py` — Test fixtures

## Exclusive Scope (files you OWN)
- `backend/errors.py` — NEW (error response helpers)
- `backend/app.py` — MODIFY (logging setup, error handlers)
- `backend/config.py` — MODIFY (add CORS_ORIGINS, fix datetime)
- `backend/extensions.py` — MODIFY (CORS from config)
- `backend/transcriptions/routes.py` — MODIFY (import new TaskService, use api_error)
- `backend/transcriptions/service.py` — MODIFY (print → logging)
- `backend/tests/test_transcriptions.py` — MODIFY

## Do NOT Modify
- `backend/auth/` (Track B owns)
- `backend/tasks/` (Track A owns — but you CONSUME its output)
- `backend/subscriptions/routes.py` (Track B owns)
- `backend/speakers/` (Track A owns db.py)

## Sub-tasks

### 1. Create `backend/errors.py`
```python
"""Unified error response helpers for the Audio Transcriber API."""
from flask import jsonify

def api_error(code: str, message: str, status: int = 400):
    """Create a standardized error response.
    
    Returns:
        tuple: (Response, status_code) in format {"error": {"code": str, "message": str}}
    """
    return jsonify({"error": {"code": code, "message": message}}), status

def not_found(message: str = "Resource not found"):
    return api_error("NOT_FOUND", message, 404)

def bad_request(message: str = "Bad request"):
    return api_error("BAD_REQUEST", message, 400)

def unauthorized(message: str = "Authentication required"):
    return api_error("AUTH_REQUIRED", message, 401)

def forbidden(message: str = "Access denied"):
    return api_error("FORBIDDEN", message, 403)

def conflict(message: str = "Resource conflict"):
    return api_error("CONFLICT", message, 409)

def server_error(message: str = "Internal server error"):
    return api_error("INTERNAL_ERROR", message, 500)
```

### 2. Configure Python logging in `backend/app.py`
In `create_app()`, add logging configuration:
```python
import logging

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO if config_name == 'production' else logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger('audio_transcriber')
    logger.info(f"Starting Audio Transcriber in {config_name} mode")
    
    # ... rest of create_app
```

Also update the global error handlers (around line 56-72) to use `api_error` from `backend.errors`.

### 3. Tighten CORS in `backend/extensions.py`
Change from:
```python
cors = CORS(origins='*')  # broad to support desktop app
```
To:
```python
from flask_cors import CORS

cors = CORS()

def init_cors(app):
    """Initialize CORS with config-based origins."""
    origins = app.config.get('CORS_ORIGINS', '*')
    if isinstance(origins, str):
        origins = [o.strip() for o in origins.split(',') if o.strip()]
    cors.init_app(app, origins=origins, supports_credentials=True)
```

### 4. Update `backend/config.py`
Add `CORS_ORIGINS` configuration:
```python
class DevelopmentConfig:
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 
                                   'http://localhost:3000,http://localhost:5099,tauri://localhost')
```

Replace all `datetime.utcnow` references with `datetime.now(timezone.utc)`.

### 5. Update `backend/transcriptions/routes.py`
- Change the import at the top from:
  ```python
  from services.task_service import TaskService
  ```
  To:
  ```python
  from backend.tasks.service import TaskService
  ```
- Use `from backend.errors import api_error, not_found, bad_request` for error responses
- Replace inline `jsonify({"error": ...})` calls with the helper functions

### 6. Replace print() with logging in `backend/transcriptions/service.py`
- Add `import logging` and `logger = logging.getLogger(__name__)` at top
- Replace all `print(f"...")` with appropriate `logger.info(...)`, `logger.warning(...)`, or `logger.error(...)`
- Keep emoji prefixes in log messages for readability (they work fine in log output)
- Example: `print(f"✅ Chunk {i} transcribed")` → `logger.info(f"✅ Chunk {i} transcribed")`

### 7. Replace `datetime.utcnow()` globally
In all files within your scope, replace:
```python
datetime.utcnow()
```
With:
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

### 8. Update `backend/tests/test_transcriptions.py`
- Ensure error responses match the new `{"error": {"code": ..., "message": ...}}` format
- Test that unauthorized requests return proper error structure

## Acceptance Criteria
```bash
python -m py_compile backend/errors.py
python -m py_compile backend/app.py
python -m py_compile backend/config.py
python -m py_compile backend/extensions.py
python -m py_compile backend/transcriptions/routes.py
python -m py_compile backend/transcriptions/service.py
# No print() calls remain in transcriptions service:
! grep -n "print(" backend/transcriptions/service.py
python -c "from backend.errors import api_error, not_found, bad_request"
python -m pytest backend/tests/ -v
```

## Important Notes

### Dependency on Track A
This track's change to `backend/transcriptions/routes.py` (importing from `backend.tasks.service`) depends on Track A creating that module. If Track A has not completed:
- Keep a comment: `# TODO: from backend.tasks.service import TaskService`
- Use a try/except fallback: 
  ```python
  try:
      from backend.tasks.service import TaskService
  except ImportError:
      from services.task_service import TaskService
  ```

## Environment
- Python 3.13+, dependencies in requirements.txt
- If dependency install fails, skip tests, focus on syntax correctness
- Verification priority: `python -m py_compile` > import check > tests
