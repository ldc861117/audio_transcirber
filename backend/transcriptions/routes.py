import uuid
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, g, current_app
from .service import TranscriptionService, tasks
from .audio_utils import SUPPORTED_EXTENSIONS, UPLOAD_DIR, DEFAULT_MAX_CHUNK_MINUTES, DEFAULT_MAX_CHUNK_MB
from .gemini_provider import BUILTIN_PROVIDERS, _get_builtin_key
from backend.errors import make_error_response
from backend.auth.decorators import jwt_required

# Import TaskService with fallback
try:
    from backend.tasks.service import TaskService
except ImportError:
    try:
        from services.task_service import TaskService
    except ImportError:
        TaskService = None

transcription_bp = Blueprint('transcriptions', __name__)


def _get_uid():
    """Get user ID from g.current_user (set by jwt_required) or fallback to g.user_id."""
    user = getattr(g, 'current_user', None)
    if user and hasattr(user, 'id'):
        return user.id
    return getattr(g, 'user_id', 0)


def _get_legacy_uid(username):
    """Look up the legacy user_id from data/users.db by username.
    Returns the legacy user_id or None if not found."""
    try:
        import sqlite3
        from app_paths import get_data_dir
        db_path = os.path.join(get_data_dir(), 'users.db')
        if not os.path.exists(db_path):
            return None
        conn = sqlite3.connect(db_path)
        row = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return row[0] if row else None
    except Exception:
        return None

@transcription_bp.route("/upload", methods=["POST"])
@jwt_required
def upload():
    file = request.files.get("audio")
    if not file:
        return make_error_response("BAD_REQUEST", "未收到音频文件", 400)

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return make_error_response("BAD_REQUEST", f"不支持的格式 {ext}，支持: {supported}", 400)

    raw_key = request.form.get("api_key", "").strip()
    provider    = request.form.get("provider", "openai")

    # Built-in provider: use hardcoded config + server-side API key
    builtin = BUILTIN_PROVIDERS.get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model    = request.form.get("model", "").strip() or builtin["model"]
        api_key  = _get_builtin_key(provider)
        if not api_key:
            return make_error_response("CONFIG_MISSING", f"服务端未配置 {builtin['api_key_env']}，请联系管理员", 400)
    else:
        # Simplified: no TEST_MODE handling for now in V2 routes, 
        # API keys should come from request or backend config.
        base_url  = request.form.get("base_url", "").strip()
        api_key   = raw_key
        model     = request.form.get("model", "").strip()

    if not all([base_url, api_key, model]):
        return make_error_response("BAD_REQUEST", "请填写 Base URL、API Key 和 Model", 400)

    max_minutes = int(request.form.get("max_minutes", DEFAULT_MAX_CHUNK_MINUTES))
    max_mb      = int(request.form.get("max_mb", DEFAULT_MAX_CHUNK_MB))
    enable_diarization = request.form.get("enable_diarization", "false").lower() == "true"

    # Save uploaded file
    task_id = uuid.uuid4().hex[:12]
    save_path = str(UPLOAD_DIR / f"{task_id}{ext}")
    file.save(save_path)

    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)

    # Use user from g (set by jwt_required)
    uid = _get_uid()

    # Pre-populate task metadata so list_tasks can return it immediately
    if uid not in tasks:
        tasks[uid] = {}
    tasks[uid][task_id] = {
        "id": task_id,
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "enable_diarization": enable_diarization,
        "status": "queued",
        "chunk_results": [],
        "completed_chunks": 0,
        "total_chunks": 0,
        "transcript": "",
        "error": "",
        "speakers": [],
    }

    # Persist to SQLite DB so the task survives server restarts
    try:
        if TaskService:
            TaskService.create_task(
                task_id=task_id,
                user_id=uid,
                filename=file.filename,
                file_size_mb=round(file_size_mb, 2),
                enable_diarization=enable_diarization,
                provider=provider,
                model=request.form.get("model", "").strip(),
            )
    except Exception as e:
        current_app.logger.error(f"Failed to persist task to DB: {e}")

    # Background transcription
    t = threading.Thread(
        target=TranscriptionService.run_transcription,
        args=(task_id, save_path, base_url, api_key, model,
              max_minutes, max_mb, provider, uid, enable_diarization),
        daemon=True,
    )
    t.start()

    return jsonify({"data": {"task_id": task_id, "file_size_mb": round(file_size_mb, 2)}})


@transcription_bp.route("/<task_id>", methods=["GET"])
@jwt_required
def status(task_id):
    uid = _get_uid()
    user_tasks = tasks.get(uid, {})
    task = user_tasks.get(task_id)
    if task:
        return jsonify({"data": task})

    # Also try user_id=0 (unauthenticated / mock auth)
    if uid != 0:
        task = tasks.get(0, {}).get(task_id)
        if task:
            return jsonify({"data": task})

    # Fallback: check database for persisted tasks
    if TaskService:
        try:
            db_task = TaskService.get_task(task_id, uid)
            if db_task:
                return jsonify({"data": db_task})
            # Try with legacy user ID
            user = getattr(g, 'current_user', None)
            if user and hasattr(user, 'username'):
                legacy_uid = _get_legacy_uid(user.username)
                if legacy_uid and legacy_uid != uid:
                    db_task = TaskService.get_task(task_id, legacy_uid)
                    if db_task:
                        return jsonify({"data": db_task})
        except Exception as e:
            current_app.logger.error(f"Error fetching task from DB: {e}")

    return make_error_response("NOT_FOUND", "任务不存在", 404)

@transcription_bp.route("/", methods=["GET"])
@jwt_required
def list_tasks():
    uid = _get_uid()
    per_page = int(request.args.get('per_page', 15))
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').strip().lower()

    # 1. Query persisted tasks from SQLite database
    db_items = []
    if TaskService:
        try:
            # Query with current V2 user ID
            db_result = TaskService.list_tasks(
                user_id=uid, page=1, per_page=9999, search=search
            )
            db_items = db_result.get("items", []) if isinstance(db_result, dict) else []

            # Also query with legacy user ID if different
            user = getattr(g, 'current_user', None)
            if user and hasattr(user, 'username'):
                legacy_uid = _get_legacy_uid(user.username)
                if legacy_uid and legacy_uid != uid:
                    legacy_result = TaskService.list_tasks(
                        user_id=legacy_uid, page=1, per_page=9999, search=search
                    )
                    legacy_items = legacy_result.get("items", []) if isinstance(legacy_result, dict) else []
                    existing_ids = {t["id"] for t in db_items}
                    for item in legacy_items:
                        if item["id"] not in existing_ids:
                            db_items.append(item)
        except Exception as e:
            current_app.logger.error(f"Error listing tasks from DB: {e}")

    # 2. Gather in-memory active tasks (not yet persisted to DB)
    user_tasks = dict(tasks.get(uid, {}))
    if uid != 0:
        user_tasks.update(tasks.get(0, {}))

    db_ids = {t["id"] for t in db_items}

    mem_items = []
    for tid, tdata in user_tasks.items():
        if tid in db_ids:
            continue  # Already in DB, skip duplicate
        item = {
            "id": tid,
            "filename": tdata.get("filename", f"task_{tid}"),
            "status": tdata.get("status", "unknown"),
            "created_at": tdata.get("created_at"),
            "file_size_mb": tdata.get("file_size_mb"),
            "provider": tdata.get("provider"),
            "enable_diarization": tdata.get("enable_diarization", False),
            "duration_seconds": tdata.get("duration_seconds", 0),
        }
        if search and search not in (item.get('filename') or '').lower():
            continue
        mem_items.append(item)

    # 3. Merge: in-memory active tasks first, then DB records
    all_items = mem_items + db_items
    all_items.sort(key=lambda x: x.get('created_at') or '', reverse=True)

    total = len(all_items)
    total_pages = max(1, -(-total // per_page))  # ceil division
    start = (page - 1) * per_page
    end = start + per_page
    page_items = all_items[start:end]

    return jsonify({
        "items": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    })

@transcription_bp.route("/<task_id>", methods=["DELETE"])
@jwt_required
def delete_task(task_id):
    # Implementation for deleting a task
    return jsonify({"data": {"success": True}})

@transcription_bp.route("/<task_id>/speakers", methods=["POST"])
@jwt_required
def update_speakers(task_id):
    # Implementation for updating speakers
    return jsonify({"data": {"success": True}})

@transcription_bp.route("/providers", methods=["GET"])
@jwt_required
def get_providers():
    available = {}
    for name, info in BUILTIN_PROVIDERS.items():
        has_key = bool(_get_builtin_key(name))
        available[name] = {
            "available": has_key,
            "model": info["model"],
        }
    return jsonify({"data": available})

@transcription_bp.route("/test-connection", methods=["POST"])
@jwt_required
def test_connection():
    # Logic similar to app.py's test_connection
    return jsonify({"data": {"ok": True}})
