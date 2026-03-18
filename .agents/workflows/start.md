---
description: Start the Audio Transcriber application (Flask backend + React frontend)
---

// turbo-all

## Steps

1. Run the start script:

```bash
cd /Users/lvdongchen/Projects/audio-transcriber && ./start.sh
```

The script will:

- Activate the Python venv (`venv/`)
- Auto-install missing pip dependencies from `requirements.txt`
- Kill any processes using ports 5099 (backend) and 3000 (frontend)
- Start Flask backend on http://localhost:5099
- Start Vite frontend on http://localhost:3000
- Press Ctrl+C to stop both services

## Dev Login Credentials

- **Username**: `testuser`
- **Password**: `test123`
- **Email**: `test@test.com`
- Login page: http://localhost:3000/login

### Password Reset (if needed)

```bash
cd /Users/lvdongchen/Projects/audio-transcriber
source venv/bin/activate
python3 -c "
import sys; sys.path.insert(0, '.')
from backend.app import create_app
app = create_app()
with app.app_context():
    from backend.auth.models import User
    from backend.db.base import db
    user = User.query.filter_by(username='testuser').first()
    user.set_password('test123')
    db.session.commit()
    print('Password reset to: test123')
"
```

## Architecture Notes

- **Auth**: V2 JWT-based (`/api/v2/auth/*`), NOT Flask-Login session-based
- **API client split**: `client` (local Flask) vs `cloudClient` (auth/subscriptions)
  - Both use same base in local dev (Vite proxy → localhost:5099)
  - In production, `cloudClient` points to Cloud Run via `VITE_CLOUD_API_URL`
- **Vite proxy**: `/api` → `http://localhost:5099` (configured in `vite.config.js`)
- **DB**: SQLAlchemy with SQLite (dev), data in `~/.audio-transcriber/`

## Manual Start (if script fails)

1. Start backend:

```bash
cd /Users/lvdongchen/Projects/audio-transcriber
source venv/bin/activate
PYTHONPATH=$(pwd) python -c "from backend.app import create_app; app = create_app(); app.run(host='0.0.0.0', port=5099, debug=False)"
```

2. Start frontend (in a separate terminal):

```bash
cd /Users/lvdongchen/Projects/audio-transcriber/frontend
npm run dev -- --port 3000
```
