import uuid
import os
import threading
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, g
from .service import TranscriptionService, tasks
from .audio_utils import SUPPORTED_EXTENSIONS, UPLOAD_DIR, DEFAULT_MAX_CHUNK_MINUTES, DEFAULT_MAX_CHUNK_MB
from .gemini_provider import BUILTIN_PROVIDERS, _get_builtin_key

# Mock jwt_required if not available from Track A
try:
    from backend.auth.routes import jwt_required
except ImportError:
    def jwt_required(f):
        return f

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
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "\u672a\u6536\u5230\u97f3\u9891\u6587\u4ef6"}}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return jsonify({"error": {"code": "BAD_REQUEST", "message": f"\u4e0d\u652f\u6301\u7684\u683c\u5f0f {ext}\uff0c\u652f\u6301: {supported}"}}), 400

    raw_key = request.form.get("api_key", "").strip()
    provider    = request.form.get("provider", "openai")

    # Built-in provider: use hardcoded config + server-side API key
    builtin = BUILTIN_PROVIDERS.get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model    = request.form.get("model", "").strip() or builtin["model"]
        api_key  = _get_builtin_key(provider)
        if not api_key:
            return jsonify({"error": {"code": "CONFIG_MISSING", "message": f"\u670d\u52a1\u7aef\u672a\u914d\u7f6e {builtin['api_key_env']}\uff0c\u8bf7\u8054\u7cfb\u7ba1\u7406\u5458"}}), 400
    else:
        # Simplified: no TEST_MODE handling for now in V2 routes, 
        # API keys should come from request or backend config.
        base_url  = request.form.get("base_url", "").strip()
        api_key   = raw_key
        model     = request.form.get("model", "").strip()

    if not all([base_url, api_key, model]):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "\u8bf7\u586b\u5199 Base URL\u3001API Key \u548c Model"}}), 400

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
        from services.task_service import TaskService
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
        print(f"⚠️ Failed to persist task to DB: {e}")

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

    # Fallback: check SQLite database for persisted tasks
    try:
        from services.task_service import TaskService
        # Try with current V2 user ID
        db_task = TaskService.get_task(task_id, uid)
        if db_task:
            return jsonify({"data": db_task})
        # Try with legacy user ID (different DB, may have different IDs)
        user = getattr(g, 'current_user', None)
        if user and hasattr(user, 'username'):
            legacy_uid = _get_legacy_uid(user.username)
            if legacy_uid and legacy_uid != uid:
                db_task = TaskService.get_task(task_id, legacy_uid)
                if db_task:
                    return jsonify({"data": db_task})
    except Exception:
        pass

    return jsonify({"error": {"code": "NOT_FOUND", "message": "\u4efb\u52a1\u4e0d\u5b58\u5728"}}), 404

@transcription_bp.route("/", methods=["GET"])
@jwt_required
def list_tasks():
    uid = _get_uid()
    per_page = int(request.args.get('per_page', 15))
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').strip().lower()

    # 1. Query persisted tasks from SQLite database
    db_items = []
    try:
        from services.task_service import TaskService
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
        import traceback
        traceback.print_exc()

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
