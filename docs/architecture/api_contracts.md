# Audio Transcriber API Contracts

> **This is the authoritative API specification.** All endpoints MUST conform to these conventions.
> Last updated: 2026-03-20

## Response Envelope

### Success

```json
{
  "data": { ... }
}
```

With pagination:

```json
{
  "data": [ ... ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}
```

### Error

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `BAD_REQUEST` | 400 | Missing or invalid parameters |
| `AUTH_REQUIRED` | 401 | Missing or expired token |
| `TOKEN_INVALID` | 401 | Invalid refresh token |
| `UNAUTHORIZED` | 401 | Wrong credentials |
| `USER_SUSPENDED` | 403 | Account suspended |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `QUOTA_EXCEEDED` | 403 | Plan quota exceeded |
| `INSUFFICIENT_PLAN` | 403 | Feature requires higher tier |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Duplicate resource |
| `STRIPE_ERROR` | 500 | Payment provider failure |
| `CONFIG_MISSING` | 500 | Server misconfiguration |
| `INTERNAL_ERROR` | 500 | Unhandled server error |

---

## Authentication

All protected endpoints require `Authorization: Bearer <access_token>` header.  
Token refresh: `POST /api/v2/auth/refresh` with `{"refresh_token": "..."}`.

---

## Endpoint Registry

### Auth (`/api/v2/auth`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Register new user |
| POST | `/login` | No | Login |
| POST | `/refresh` | No | Refresh access token |
| POST | `/logout` | No | Revoke refresh token |
| GET | `/me` | Yes | Get current user profile |
| PUT | `/me` | Yes | Update profile (username, email) |
| POST | `/change-password` | Yes | Change password |

**POST `/register`**  
Request: `{"username": str, "email": str, "password": str}`  
Response: `{"data": {"access_token": str, "refresh_token": str, "user": {id, username, email, role, tier}}}`

**POST `/login`**  
Request: `{"username": str, "password": str}` (username or email accepted)  
Response: same as register

**POST `/refresh`**  
Request: `{"refresh_token": str}`  
Response: `{"data": {"access_token": str}}`

**GET `/me`**  
Response: `{"data": {id, username, email, role, status, email_verified, tier, created_at, last_login_at}}`

---

### Subscriptions (`/api/v2/subscriptions`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/plans` | No | List available plans |
| GET | `/me` | Yes | Current subscription status |
| POST | `/checkout` | Yes | Create Stripe checkout session |
| POST | `/cancel` | Yes | Cancel subscription |
| POST | `/reactivate` | Yes | Reactivate cancelled subscription |
| GET | `/usage` | Yes | Current usage summary |
| GET | `/invoices` | Yes | Payment history |
| POST | `/portal` | Yes | Create Stripe billing portal URL |
| POST | `/webhook` | No* | Stripe webhook (*signature verified) |

---

### Transcriptions (`/api/v2/transcriptions`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/upload` | Yes | Upload audio and start transcription |
| GET | `/` | Yes | List transcription tasks (paginated) |
| GET | `/<task_id>` | Yes | Get task status/result |
| DELETE | `/<task_id>` | Yes | Delete a task |
| POST | `/<task_id>/speakers` | Yes | Update speaker labels |
| GET | `/providers` | Yes | Available transcription providers |
| POST | `/test-connection` | Yes | Test API provider connectivity |

**POST `/upload`**  
Request: `multipart/form-data` with fields:
- `audio` (file, required)
- `provider` (str, default: "gemini")
- `model` (str, optional)
- `base_url` (str, for custom provider)
- `api_key` (str, for custom provider)
- `max_minutes` (int, default: 60)
- `max_mb` (int, default: 100)
- `enable_diarization` (bool, default: false)

Response: `{"data": {"task_id": str, "file_size_mb": float}}`

**GET `/`**  
Params: `page`, `per_page`  
Response: `{"data": [...], "meta": {total, page, per_page, total_pages}}`

**GET `/<task_id>`**  
Response: `{"data": {status, filename, transcript, speakers, error, ...}}`

---

### Speakers (`/api/v2/speakers`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | List user's speaker profiles |
| POST | `/<id>/name` | Yes | Rename a speaker |
| DELETE | `/<id>` | Yes | Delete a speaker profile |
| POST | `/merge` | Yes | Merge two speakers |
| GET | `/clips/<filename>` | Yes | Serve audio clip |

---

### Export (`/api/v2/export`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/<task_id>` | Yes | Download transcript (format via `?format=txt\|md\|srt\|docx\|pdf`) |

---

### Recordings (`/api/v2/recordings`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/start` | Yes | Start a recording session |
| POST | `/<session_id>/chunk` | Yes | Append audio chunk |
| POST | `/<session_id>/finalize` | Yes | Finalize recording, optionally auto-transcribe |

---

### System

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/health` | No | Health check |

---

## Frontend ↔ Backend Mapping

| Frontend `endpoints.js` | Backend Route | Status |
|------------------------|---------------|--------|
| `api.auth.*` | `backend/auth/routes.py` | ✅ |
| `api.subscriptions.*` | `backend/subscriptions/routes.py` | ✅ |
| `api.transcriptions.upload` | `backend/transcriptions/routes.py` | ⚠️ works but no DB persist |
| `api.transcriptions.list` | `backend/transcriptions/routes.py` | ⚠️ memory only |
| `api.transcriptions.status` | `backend/transcriptions/routes.py` | ⚠️ no DB fallback |
| `api.transcriptions.delete` | `backend/transcriptions/routes.py` | ❌ stub |
| `api.transcriptions.updateSpeakers` | `backend/transcriptions/routes.py` | ❌ stub |
| `api.transcriptions.testConnection` | `backend/transcriptions/routes.py` | ❌ stub |
| `api.speakers.*` | `backend/speakers/routes.py` | ✅ implemented |
| `api.exports.download` | `backend/exports/routes.py` | ⚠️ no DB-backed task lookup |
| `api.recordings.*` | `backend/recordings/routes.py` | ✅ |
