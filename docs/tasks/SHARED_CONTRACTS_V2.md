# Shared Contracts V2 — Frontend-Backend Separation

> **ALL parallel Tracks MUST read and conform to these contracts.**
> **NO Track should modify this file.**

---

## 1. Tech Stack

| Layer             | Technology                       | Notes                               |
| ----------------- | -------------------------------- | ----------------------------------- |
| Backend Framework | Flask 3.x                        | Factory pattern (`create_app()`)    |
| ORM               | SQLAlchemy 2.x + Alembic         | Abstract DB layer                   |
| Auth              | PyJWT                            | Custom JWT (not flask-jwt-extended) |
| Database          | SQLite (dev) / PostgreSQL (prod) | Via SQLAlchemy URI                  |
| Payment           | Stripe Python SDK                | Checkout + Webhooks                 |
| Frontend          | React 19 + Vite 7                | Zustand, react-router-dom, axios    |
| Styling           | Vanilla CSS                      | Existing approach                   |

## 2. Directory Ownership

```
audio-transcriber/
├── backend/
│   ├── app.py                  # Track C owns (factory function)
│   ├── config.py               # Track E owns
│   ├── extensions.py           # Track E owns
│   ├── auth/                   # Track A ONLY
│   ├── subscriptions/          # Track B ONLY
│   ├── transcriptions/         # Track C ONLY
│   ├── speakers/               # Track C ONLY
│   ├── exports/                # Track C ONLY
│   ├── db/                     # Track E creates base, all read
│   │   ├── base.py             # SQLAlchemy Base + engine
│   │   └── migrations/         # Alembic
│   └── tests/                  # Each Track owns its tests
├── frontend/                   # Track D ONLY
└── docs/tasks/                 # Read-only reference
```

## 3. Database Models (SQLAlchemy)

All models inherit from `db.Model` defined in `backend/db/base.py`.

### 3.1 User (Track A owns)

```python
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')        # user | admin
    status = db.Column(db.String(20), default='active')    # active | suspended | deleted
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    subscription = db.relationship('Subscription', backref='user', uselist=False, lazy='joined')
```

### 3.2 RefreshToken (Track A owns)

```python
class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3.3 Subscription (Track B owns)

```python
class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    tier = db.Column(db.String(20), default='free')              # free | basic | pro
    billing_cycle = db.Column(db.String(10), nullable=True)      # monthly | yearly | None(free)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='active')          # active | cancelled | past_due
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    monthly_minutes_limit = db.Column(db.Integer, default=60)
    minutes_used = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3.4 QuotaUsage (Track B owns)

```python
class QuotaUsage(db.Model):
    __tablename__ = 'quota_usage'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(64), nullable=False)
    minutes_used = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 3.5 Transcription (Track C owns)

```python
class Transcription(db.Model):
    __tablename__ = 'transcriptions'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_size_mb = db.Column(db.Float, nullable=False)
    transcript = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='queued')
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    enable_diarization = db.Column(db.Boolean, default=False)
    speakers_json = db.Column(db.Text, default='')
    error = db.Column(db.Text, default='')
    provider = db.Column(db.String(50), default='')
    model = db.Column(db.String(100), default='')
    chunk_count = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Float, default=0.0)
```

### 3.6 Invoice (Track B owns)

```python
class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Integer, nullable=False)    # cents
    currency = db.Column(db.String(3), default='cny')
    status = db.Column(db.String(20))                 # paid | failed | refunded
    description = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## 4. API Conventions

### 4.1 Route Prefix

ALL routes use `/api/v2/` prefix:

```
/api/v2/auth/           — Track A
/api/v2/subscriptions/  — Track B
/api/v2/transcriptions/ — Track C
/api/v2/speakers/       — Track C
/api/v2/export/         — Track C
```

### 4.2 Response Format

```json
// Success (single resource)
{ "data": { "id": 1, "username": "john" } }

// Success (list with pagination)
{ "data": [...], "meta": { "total": 100, "page": 1, "per_page": 20, "total_pages": 5 } }

// Error
{ "error": { "code": "QUOTA_EXCEEDED", "message": "月度配额已用完" } }
```

### 4.3 HTTP Status Codes

| Code | Meaning                                    |
| ---- | ------------------------------------------ |
| 200  | Success                                    |
| 201  | Created                                    |
| 400  | Bad request / validation error             |
| 401  | Not authenticated (missing/expired JWT)    |
| 403  | Forbidden (insufficient plan / wrong role) |
| 404  | Resource not found                         |
| 409  | Conflict (duplicate)                       |
| 429  | Rate limited                               |
| 500  | Internal error                             |

### 4.4 Error Codes

| Code                | Trigger                            |
| ------------------- | ---------------------------------- |
| `AUTH_REQUIRED`     | No JWT token                       |
| `TOKEN_EXPIRED`     | JWT expired                        |
| `TOKEN_INVALID`     | JWT signature invalid              |
| `INSUFFICIENT_PLAN` | Feature requires higher tier       |
| `QUOTA_EXCEEDED`    | Monthly minutes exhausted          |
| `FILE_TOO_LARGE`    | Exceeds plan's max file size       |
| `DURATION_TOO_LONG` | Exceeds plan's max single duration |
| `USER_SUSPENDED`    | Account suspended                  |
| `PAYMENT_REQUIRED`  | Subscription past_due              |

## 5. JWT Token Spec

### 5.1 Access Token (15 min)

```json
{
  "sub": 42,
  "username": "john",
  "role": "user",
  "tier": "pro",
  "iat": 1709855100,
  "exp": 1709856000,
  "type": "access"
}
```

Header: `Authorization: Bearer <access_token>`

### 5.2 Refresh Token (7 days)

```json
{
  "sub": 42,
  "jti": "unique-token-id",
  "iat": 1709855100,
  "exp": 1710459900,
  "type": "refresh"
}
```

Sent via POST body to `/api/v2/auth/refresh`.

### 5.3 Token Refresh Flow

```
Client → POST /api/v2/auth/refresh { "refresh_token": "xxx" }
Server → Check token valid + not revoked
       → Issue new access_token
       → Return { "data": { "access_token": "new_xxx" } }
```

## 6. Plan Definitions

```python
PLAN_DEFINITIONS = {
    "free": {
        "display_name": "免费版",
        "price_monthly_cents": 0,
        "price_yearly_cents": 0,
        "stripe_price_id_monthly": None,
        "stripe_price_id_yearly": None,
        "monthly_minutes": 60,
        "max_single_minutes": 30,
        "max_file_size_mb": 50,
        "features": {
            "diarization": False,
            "export_formats": ["txt", "md"],
            "priority_queue": False,
            "api_access": False,
        }
    },
    "basic": {
        "display_name": "基础版",
        "price_monthly_cents": 2900,
        "price_yearly_cents": 29000,
        "monthly_minutes": 300,
        "max_single_minutes": 120,
        "max_file_size_mb": 200,
        "features": {
            "diarization": True,
            "export_formats": ["txt", "md", "srt"],
            "priority_queue": False,
            "api_access": False,
        }
    },
    "pro": {
        "display_name": "专业版",
        "price_monthly_cents": 9900,
        "price_yearly_cents": 99000,
        "monthly_minutes": -1,
        "max_single_minutes": -1,
        "max_file_size_mb": 500,
        "features": {
            "diarization": True,
            "export_formats": ["txt", "md", "srt", "docx", "pdf"],
            "priority_queue": True,
            "api_access": True,
        }
    }
}
```

## 7. `backend/db/base.py` Template (Track E creates)

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
```

## 8. `backend/extensions.py` Template (Track E creates)

```python
from flask_cors import CORS

cors = CORS()

def init_extensions(app):
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', ['*']))
```

## 9. `backend/config.py` Template (Track E creates)

```python
import os
from datetime import timedelta

class BaseConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///data/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-change-me')
    JWT_REFRESH_SECRET_KEY = os.environ.get('JWT_REFRESH_SECRET_KEY', 'dev-refresh-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False

configs = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
```

## 10. Conventions

- **Imports**: Use relative imports within each module (e.g., `from .models import User`)
- **Tests**: Place in `backend/tests/test_<module>.py`
- **Migrations**: Use `flask db migrate` / `flask db upgrade`
- **Environment**: Python 3.11+, dependencies in `requirements.txt`
- **Error handling**: Always catch exceptions and return contract-compliant error JSON
- **Logging**: Use `app.logger` or Python `logging` module, never bare `print()`
