# Contributing Guide

## Development Setup

```bash
# 1. Clone and setup
git clone <repo-url>
cd audio-transcriber
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Start development servers
./start.sh
```

## Branch Strategy

- **`main`** — Production-ready code. Protected.
- **`feature/<name>`** — Feature branches. Create PR to merge.
- Never commit directly to `main`.

```bash
git checkout -b feature/my-feature
# ... make changes ...
git add -A && git commit -m "descriptive message"
git push origin feature/my-feature
# Create PR on GitHub
```

## Backend Conventions

### Module Structure

Every new feature module goes in `backend/<module>/`:

```
backend/<module>/
├── __init__.py       # Blueprint declaration
├── routes.py         # HTTP endpoints (thin — delegate to service)
├── service.py        # Business logic
├── models.py         # Data models (if needed)
└── db.py             # Database queries (if needed)
```

### Adding a New Endpoint

1. **Define route** in `routes.py` using the module's Blueprint
2. **Use `@jwt_required`** decorator from `backend.auth.decorators`
3. **Return responses** using `success_response()` / `error_response()` from `backend.utils.responses`
4. **Register blueprint** in `backend/app.py` with prefix `/api/v2/<module>`
5. **Document** in `docs/architecture/api_contracts.md`
6. **Update** `docs/architecture/Full_CodeMap.md` if adding new files

### API Response Envelope

All endpoints MUST use the standard envelope:

```python
# Success
from backend.utils.responses import success_response
return success_response(data={"key": "value"})
# → {"data": {"key": "value"}, "meta": {"timestamp": "..."}}

# Error  
from backend.utils.responses import error_response
return error_response("ERROR_CODE", "Human message", status_code=400)
# → {"error": {"code": "ERROR_CODE", "message": "Human message"}}
```

### Authentication

- **All protected routes** use `@jwt_required` from `backend.auth.decorators`
- Access current user ID via `g.user_id` inside protected routes
- Never use Flask-Login (`login_required`, `current_user`)

### Database Access

- **Auth/Subscription data**: Use SQLAlchemy models in `backend/db/base.py`
- **Transcription tasks**: Use `TaskService` from `backend/transcriptions/task_service.py`
- Never import from root-level `db/`, `models/`, or `services/` (deleted)

## Frontend Conventions

### File Organization

```
frontend/src/
├── api/        # All HTTP calls go here — no fetch() in components
├── pages/      # One file per route
├── components/ # Reusable, stateless when possible
├── stores/     # Zustand stores for state management
└── styles/     # Global CSS
```

### API Calls

- All API calls go through `api/` layer — never call `fetch()` directly from components
- All API endpoints use `/api/v2/` prefix
- Handle loading/error states in stores, not components

## PR Checklist

Before submitting a PR, verify:

- [ ] Backend starts: `PYTHONPATH=$(pwd) python -c "from backend.app import create_app; create_app()"`
- [ ] New endpoints use `@jwt_required` and response helpers
- [ ] New endpoints documented in `api_contracts.md`
- [ ] New files listed in `Full_CodeMap.md`
- [ ] No root-level imports (`from services.*`, `from models.*`, `from db.*`)
- [ ] Commit messages are descriptive
- [ ] No hardcoded secrets or API keys

## Code Style

- **Python**: Follow PEP 8, use type hints for function signatures
- **JavaScript**: Use ESLint defaults, prefer functional components
- **Naming**: snake_case for Python, camelCase for JavaScript
- **Imports**: Use absolute imports (`from backend.auth.decorators import ...`)
