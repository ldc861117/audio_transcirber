# Track B: Authentication & Security Consolidation

## Goal
Eliminate the mock JWT decorator in subscriptions, add security hardening, and create a desktop auth adapter for Flask-Login replacement.

## Must Read Before Starting
- `docs/refactor/SHARED_CONTRACTS.md` — Auth contract and desktop adapter API
- `backend/auth/decorators.py` — The REAL `@jwt_required` decorator
- `backend/auth/jwt_manager.py` — JWT token creation/verification
- `backend/auth/models.py` — User model (SQLAlchemy)
- `backend/subscriptions/routes.py` — Lines 11-31: the MOCK `jwt_required` to remove
- `auth.py` (root) — Legacy Flask-Login module to deprecate
- `backend/tests/conftest.py` — Test fixtures
- `backend/tests/test_auth.py` — Existing auth tests (reference for patterns)

## Exclusive Scope (files you OWN)
- `backend/subscriptions/routes.py` — MODIFY (replace mock decorator import ONLY)
- `backend/auth/jwt_manager.py` — MODIFY (add secret validation)
- `backend/auth/decorators.py` — MODIFY (if needed for improvements)
- `backend/auth/desktop_adapter.py` — NEW
- `auth.py` (root) — MODIFY (add deprecation warning)
- `backend/tests/test_subscriptions.py` — MODIFY (update for real auth)

## Do NOT Modify
- `backend/tasks/` (Track A owns)
- `backend/transcriptions/` (Track C owns)
- `backend/app.py` (Track C owns)
- `backend/config.py` (Track C owns)

## Sub-tasks

### 1. Remove mock `jwt_required` from subscriptions
In `backend/subscriptions/routes.py`:
- DELETE lines 11-31 (the local `jwt_required` function definition)
- ADD at the top: `from backend.auth.decorators import jwt_required`
- The rest of the file should work without changes because the real `jwt_required` also sets `g.current_user` (but as a User model instance with `.id`, `.username`, `.email` attributes)

### 2. Add JWT secret validation
In `backend/auth/jwt_manager.py`, add a validation function:
```python
def validate_jwt_secrets():
    """Raise RuntimeError if JWT secrets contain unsafe defaults."""
    secret = current_app.config.get('JWT_SECRET_KEY', '')
    refresh_secret = current_app.config.get('JWT_REFRESH_SECRET_KEY', '')
    
    unsafe_patterns = ['change-me', 'your-secret', 'test-secret', '']
    for pattern in unsafe_patterns:
        if pattern and (pattern in secret.lower() or pattern in refresh_secret.lower()):
            import warnings
            warnings.warn(
                f"JWT secret contains unsafe pattern '{pattern}'. "
                "Set JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY to strong random values.",
                RuntimeWarning
            )
            break
```
Call this in `create_access_token` on first invocation (lazy check, not hard failure to avoid breaking dev).

### 3. Add deprecation warning to root `auth.py`
Add at the top of `auth.py`:
```python
import warnings
warnings.warn(
    "auth.py is deprecated. Use backend/auth/ for JWT-based authentication. "
    "This module is only retained for desktop app backward compatibility.",
    DeprecationWarning,
    stacklevel=2
)
```

### 4. Create `backend/auth/desktop_adapter.py`
For desktop mode (no manual login), provide automatic JWT token generation:
```python
"""
Desktop mode adapter: auto-creates a local user and issues JWT tokens.
Replaces the legacy Flask-Login get_or_create_local_user() pattern.
"""
from backend.auth.models import User, db
from backend.auth.jwt_manager import create_access_token, create_refresh_token

def get_desktop_token(app):
    """
    Get or create the 'local' desktop user and return JWT tokens.
    Returns: {"access_token": str, "refresh_token": str, "user": dict}
    """
    with app.app_context():
        user = User.query.filter_by(username='local').first()
        if not user:
            import os
            user = User(username='local', email='local@desktop.app')
            user.set_password(os.urandom(16).hex())
            db.session.add(user)
            db.session.commit()
        
        access_token = create_access_token(user.id, user.role, 
                                           getattr(user, 'subscription_tier', 'free'))
        refresh_token = create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }
```

### 5. Update subscription tests
In `backend/tests/test_subscriptions.py`:
- Remove any tests that rely on the mock decorator
- Use `auth_headers` fixture from conftest to authenticate requests
- Ensure all subscription endpoints return proper responses when JWT-authenticated

## Acceptance Criteria
```bash
python -m py_compile backend/subscriptions/routes.py
python -m py_compile backend/auth/desktop_adapter.py
python -m py_compile backend/auth/jwt_manager.py
python -c "from backend.subscriptions.routes import subscription_bp"
python -c "from backend.auth.desktop_adapter import get_desktop_token"
# Verify no local jwt_required definition remains:
! grep -n "def jwt_required" backend/subscriptions/routes.py
python -m pytest backend/tests/test_auth.py backend/tests/test_subscriptions.py -v
```

## Environment
- Python 3.13+, dependencies in requirements.txt
- If dependency install fails, skip tests, focus on syntax correctness
- Verification priority: `python -m py_compile` > import check > tests
