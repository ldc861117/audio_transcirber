# Full Code Map

## Project Root

| File | Purpose |
|---|---|
| `start.sh` | Launch script — starts Flask backend + Vite dev server |
| `app_paths.py` | Shared utility for resolving `data/` directory paths |
| `requirements.txt` | Python dependencies |
| `AGENTS.md` | Development workflow and agent SOP |
| `.env` / `.env.example` | Environment configuration |

## Backend (`backend/`)

### Core
| File | Purpose |
|---|---|
| `app.py` | Flask application factory (`create_app()`) |
| `config.py` | Configuration classes (Dev/Prod), env vars mapping |
| `extensions.py` | CORS and extension initialization |

### Auth (`backend/auth/`)
| File | Purpose |
|---|---|
| `routes.py` | Login, register, logout, refresh, profile endpoints |
| `jwt_manager.py` | JWT token creation and validation logic |
| `decorators.py` | `@jwt_required` decorator for protected routes |
| `models.py` | SQLAlchemy `User` model |
| `utils.py` | Auth helper utilities |

### Transcriptions (`backend/transcriptions/`)
| File | Purpose |
|---|---|
| `routes.py` | Upload, status, list, delete, update-speakers, test-connection |
| `service.py` | Background transcription orchestrator (split → transcribe → merge) |
| `audio_utils.py` | Audio splitting logic (`pydub`/`ffmpeg`) |
| `gemini_provider.py` | Google Gemini transcription provider |
| `task_service.py` | `TaskService` — CRUD operations for transcription tasks (SQLite) |
| `task_model.py` | `TranscriptionRecord` dataclass (DB ↔ API serialization) |

### Speakers (`backend/speakers/`)
| File | Purpose |
|---|---|
| `routes.py` | Speaker profile CRUD, voice clip management |
| `service.py` | Speaker matching, diarization logic |
| `db.py` | Speaker database queries |

### Exports (`backend/exports/`)
| File | Purpose |
|---|---|
| `routes.py` | Export transcript as SRT/TXT/DOCX |
| `service.py` | Format conversion logic |

### Subscriptions (`backend/subscriptions/`)
| File | Purpose |
|---|---|
| `routes.py` | Checkout, plans, invoices, portal, webhooks |
| `stripe_service.py` | Stripe API integration |
| `quota_service.py` | Usage quota tracking |
| `plan_config.py` | Subscription plan definitions |
| `models.py` | SQLAlchemy subscription models |

### Recordings (`backend/recordings/`)
| File | Purpose |
|---|---|
| `routes.py` | Real-time recording session management |
| `service.py` | Chunk assembly and auto-transcribe |

### Data Layer (`backend/db/`)
| File | Purpose |
|---|---|
| `base.py` | SQLAlchemy engine and `init_db()` |
| `task_db.py` | Raw SQLite connection for transcription tasks |

### Utilities (`backend/utils/`)
| File | Purpose |
|---|---|
| `responses.py` | `success_response()`, `error_response()`, `paginated_response()` |

## Frontend (`frontend/src/`)

| Directory | Purpose |
|---|---|
| `api/` | HTTP client configuration, API endpoint definitions |
| `pages/` | Route-level components (Transcribe, History, Settings, etc.) |
| `components/` | Reusable UI components |
| `stores/` | Zustand state management stores |
| `styles/` | Global CSS and design tokens |

## Documentation (`docs/`)

| File | Purpose |
|---|---|
| `architecture/ARCHITECTURE.md` | System architecture overview |
| `architecture/Full_CodeMap.md` | This file — complete file index |
| `architecture/api_contracts.md` | API response envelope and endpoint specifications |

## Runtime Data (`data/`)

| File | Purpose |
|---|---|
| `app.db` | SQLAlchemy database (users, subscriptions) |
| `tasks.db` | SQLite database (transcription tasks) |
| `uploads/` | Temporary audio file storage |
