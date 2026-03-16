"""
Recording routes for Audio Transcriber.
Provides endpoints to save recordings without transcription,
and to start transcription on saved recordings.
"""

import os
import uuid
import threading
from pathlib import Path

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.task_service import TaskService

recording_bp = Blueprint("recordings", __name__, url_prefix="/api/v1/recordings")

# Import shared config from app module (deferred to avoid circular imports)
_app_context = {}


def _get_app_context():
    """Lazy-load shared references from the main app module."""
    if not _app_context:
        import app as main_app
        _app_context["UPLOAD_DIR"] = main_app.UPLOAD_DIR
        _app_context["SUPPORTED_EXTENSIONS"] = main_app.SUPPORTED_EXTENSIONS
        _app_context["tasks"] = main_app.tasks
        _app_context["run_transcription"] = main_app.run_transcription
        _app_context["BUILTIN_PROVIDERS"] = main_app.BUILTIN_PROVIDERS
        _app_context["_get_builtin_key"] = main_app._get_builtin_key
        _app_context["DEFAULT_BASE_URL"] = main_app.DEFAULT_BASE_URL
        _app_context["DEFAULT_API_KEY"] = main_app.DEFAULT_API_KEY
        _app_context["DEFAULT_MODEL"] = main_app.DEFAULT_MODEL
        _app_context["DEFAULT_MAX_CHUNK_MINUTES"] = main_app.DEFAULT_MAX_CHUNK_MINUTES
        _app_context["DEFAULT_MAX_CHUNK_MB"] = main_app.DEFAULT_MAX_CHUNK_MB
        _app_context["DEFAULT_OVERLAP_MINUTES"] = main_app.DEFAULT_OVERLAP_MINUTES
        _app_context["TEST_MODE"] = main_app.TEST_MODE
        _app_context["SERVER_ENV_SENTINEL"] = main_app.SERVER_ENV_SENTINEL
    return _app_context


@recording_bp.route("/save", methods=["POST"])
@login_required
def save_recording():
    """Save a recording file without starting transcription.
    Creates a task record with status='recorded'.
    """
    ctx = _get_app_context()

    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "未收到音频文件"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ctx["SUPPORTED_EXTENSIONS"]:
        supported = ", ".join(sorted(ctx["SUPPORTED_EXTENSIONS"]))
        return jsonify({"error": f"不支持的格式 {ext}，支持: {supported}"}), 400

    # Save file to upload directory
    task_id = uuid.uuid4().hex[:12]
    save_path = str(ctx["UPLOAD_DIR"] / f"{task_id}{ext}")
    file.save(save_path)

    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)
    uid = current_user.id

    # Persist to SQLite with status='recorded'
    try:
        TaskService.create_task(
            task_id=task_id,
            user_id=uid,
            filename=file.filename,
            file_size_mb=round(file_size_mb, 2),
        )
        # Update status to 'recorded' (create_task defaults to 'queued')
        TaskService.update_task(task_id, status="recorded")
    except Exception as db_err:
        print(f"⚠️ DB create failed: {db_err}")
        return jsonify({"error": "保存录音失败"}), 500

    return jsonify({
        "task_id": task_id,
        "file_size_mb": round(file_size_mb, 2),
        "status": "recorded",
    })


@recording_bp.route("/<task_id>/transcribe", methods=["POST"])
@login_required
def transcribe_recording(task_id):
    """Start transcription on a previously saved recording."""
    ctx = _get_app_context()
    uid = current_user.id

    # Check if task exists and belongs to user
    task_data = TaskService.get_task(task_id, uid)
    if not task_data:
        return jsonify({"error": "录音不存在"}), 404

    if task_data["status"] not in ("recorded", "error"):
        return jsonify({"error": "该录音已在转写中或已完成"}), 400

    # Find the saved file
    upload_dir = ctx["UPLOAD_DIR"]
    save_path = None
    for f in upload_dir.iterdir():
        if f.stem == task_id:
            save_path = str(f)
            break

    if not save_path or not os.path.exists(save_path):
        return jsonify({"error": "录音文件已丢失，请重新录制"}), 404

    # Get transcription config from request body
    data = request.json or {}
    provider = data.get("provider", "gemini")
    model = data.get("model", "")
    raw_key = data.get("api_key", "").strip()
    base_url = data.get("base_url", "").strip()
    enable_diarization = data.get("enable_diarization", False)

    # Resolve provider config
    builtin = ctx["BUILTIN_PROVIDERS"].get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model = model or builtin["model"]
        api_key = ctx["_get_builtin_key"](provider)
        if not api_key:
            return jsonify({"error": f"服务端未配置 {builtin['api_key_env']}，请联系管理员"}), 400
    else:
        use_server_key = ctx["TEST_MODE"] and (not raw_key or raw_key == ctx["SERVER_ENV_SENTINEL"])
        base_url = base_url or ctx["DEFAULT_BASE_URL"]
        api_key = ctx["DEFAULT_API_KEY"] if use_server_key else (raw_key or ctx["DEFAULT_API_KEY"])
        model = model or ctx["DEFAULT_MODEL"]

    if not all([base_url, api_key, model]):
        return jsonify({"error": "请配置 API 参数"}), 400

    max_minutes      = int(data.get("max_minutes", ctx["DEFAULT_MAX_CHUNK_MINUTES"]))
    max_mb           = int(data.get("max_mb", ctx["DEFAULT_MAX_CHUNK_MB"]))
    overlap_minutes  = int(data.get("overlap_minutes", ctx["DEFAULT_OVERLAP_MINUTES"]))

    # Create in-memory task for live progress tracking
    tasks = ctx["tasks"]
    if uid not in tasks:
        tasks[uid] = {}

    tasks[uid][task_id] = {
        "status": "queued",
        "filename": task_data["filename"],
        "file_size_mb": task_data["file_size_mb"],
        "total_chunks": 0,
        "current_chunk": 0,
        "completed_chunks": 0,
        "chunk_results": [],
        "transcript": "",
        "error": "",
        "speakers": [],
        "diarization_error": "",
        "enable_diarization": enable_diarization,
    }

    # Update DB status
    TaskService.update_task(
        task_id,
        status="queued",
        provider=provider,
        model=model,
        enable_diarization=enable_diarization,
    )

    # Start transcription in background
    t = threading.Thread(
        target=ctx["run_transcription"],
        args=(task_id, save_path, base_url, api_key, model,
              max_minutes, max_mb, provider, uid, enable_diarization,
              overlap_minutes),
        daemon=True,
    )
    t.start()

    return jsonify({"ok": True, "task_id": task_id, "status": "queued"})
