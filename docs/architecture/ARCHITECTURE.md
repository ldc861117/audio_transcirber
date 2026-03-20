# Audio Transcriber Architecture

## Overview

Audio Transcriber is a SaaS web application for splitting large audio files and transcribing them via OpenAI-compatible APIs. The system uses a **decoupled frontend/backend** architecture with JWT authentication and Stripe-integrated subscriptions.

## System Architecture

```
┌──────────────────┐         ┌──────────────────────────────┐
│  React Frontend  │  HTTP   │       Flask Backend           │
│  (Vite :3000)    │ ◄─────► │       (API :5099)             │
│                  │  JSON   │                               │
│  pages/          │         │  api/v2/auth/*                │
│  components/     │         │  api/v2/transcriptions/*      │
│  stores/         │         │  api/v2/speakers/*            │
│  api/            │         │  api/v2/subscriptions/*       │
└──────────────────┘         │  api/v2/export/*              │
                             │  api/v2/recordings/*          │
                             └──────────┬───────────────────┘
                                        │
                             ┌──────────▼───────────────────┐
                             │     Data Layer                │
                             │  SQLite (data/tasks.db)       │
                             │  SQLAlchemy (data/app.db)     │
                             └──────────────────────────────┘
```

## Backend Modules (`backend/`)

| Module | Prefix | Responsibility |
|---|---|---|
| `auth/` | `/api/v2/auth` | JWT login/register, token refresh, user profile |
| `transcriptions/` | `/api/v2/transcriptions` | Upload, split, transcribe, status polling, speaker labeling |
| `speakers/` | `/api/v2/speakers` | Speaker profile CRUD, voice clip management |
| `exports/` | `/api/v2/export` | Export transcripts (SRT, TXT, DOCX) |
| `subscriptions/` | `/api/v2/subscriptions` | Stripe checkout, plans, invoices, webhooks |
| `recordings/` | `/api/v2/recordings` | Real-time recording sessions (chunk upload) |
| `db/` | — | Database connections (SQLite for tasks, SQLAlchemy for auth) |
| `utils/` | — | Shared response helpers (`success_response`, `error_response`) |

### Module Structure (Convention)

Each module follows a consistent pattern:
```
backend/<module>/
├── __init__.py       # Blueprint declaration
├── routes.py         # HTTP endpoint definitions
├── service.py        # Business logic
├── models.py         # SQLAlchemy/dataclass models (if needed)
└── db.py             # Database queries (if needed)
```

## Frontend (`frontend/`)

Built with **React + Vite**, organized by feature:

```
frontend/src/
├── api/              # HTTP client, endpoints config
├── pages/            # Route-level page components
├── components/       # Reusable UI components
├── stores/           # Zustand state management
└── styles/           # Global CSS
```

## Authentication Flow

1. User registers/logs in → Backend issues **JWT access token** (15min) + **refresh token** (7 days)
2. Frontend stores tokens → Sends `Authorization: Bearer <token>` with every request
3. `@jwt_required` decorator on protected routes validates tokens
4. Token refresh happens transparently when access token expires

## Transcription Data Flow

1. **Upload**: User uploads audio → saved to `data/uploads/`
2. **Split**: `audio_utils.py` splits file by duration/size constraints using `pydub`
3. **Transcribe**: `service.py` spawns background thread → sends chunks to API
4. **Persist**: Results saved to SQLite via `TaskService`
5. **Poll**: Frontend polls `GET /api/v2/transcriptions/<task_id>` for progress

## Key Dependencies

| Package | Purpose |
|---|---|
| `flask` | Web framework |
| `flask-sqlalchemy` | ORM for auth/subscription data |
| `pyjwt` | JWT token management |
| `pydub` | Audio file processing (requires `ffmpeg`) |
| `openai` | OpenAI-compatible API client |
| `stripe` | Payment processing |
| `google-genai` | Gemini provider support |

## Configuration

- **Environment**: `.env` file at project root (see `.env.example`)
- **Config class**: `backend/config.py` (Development / Production)
- **Databases**: `data/app.db` (SQLAlchemy), `data/tasks.db` (raw SQLite)

## Running

```bash
./start.sh    # Starts backend (:5099) + frontend (:3000)
```
