import uuid
import os
import threading
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify, g

from backend.auth.decorators import jwt_required
from backend.utils.responses import (
    success_response, error_response, paginated_response,
    bad_request, not_found, internal_error,
)
from .service import TranscriptionService, tasks
from .audio_utils import SUPPORTED_EXTENSIONS, UPLOAD_DIR, DEFAULT_MAX_CHUNK_MINUTES, DEFAULT_MAX_CHUNK_MB
from .gemini_provider import BUILTIN_PROVIDERS, _get_builtin_key

logger = logging.getLogger(__name__)

transcription_bp = Blueprint('transcriptions', __name__)


# ── Helpers ──

def _get_uid():
    return g.current_user.id if getattr(g, 'current_user', None) else 0


# ── Upload ──

@transcription_bp.route("/upload", methods=["POST"])
@jwt_required
def upload():
    file = request.files.get("audio")
    if not file:
        return bad_request("未收到音频文件")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return bad_request(f"不支持的格式 {ext}，支持: {supported}")

    provider = request.form.get("provider", "openai")

    # Built-in provider: server-side key
    builtin = BUILTIN_PROVIDERS.get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model = request.form.get("model", "").strip() or builtin["model"]
        api_key = _get_builtin_key(provider)
        if not api_key:
            return error_response("CONFIG_MISSING",
                                  f"服务端未配置 {builtin['api_key_env']}，请联系管理员", 400)
    else:
        base_url = request.form.get("base_url", "").strip()
        api_key = request.form.get("api_key", "").strip()
        model = request.form.get("model", "").strip()

    if not all([base_url, api_key, model]):
        return bad_request("请填写 Base URL、API Key 和 Model")

    max_minutes = int(request.form.get("max_minutes", DEFAULT_MAX_CHUNK_MINUTES))
    max_mb = int(request.form.get("max_mb", DEFAULT_MAX_CHUNK_MB))
    enable_diarization = request.form.get("enable_diarization", "false").lower() == "true"

    # Save uploaded file
    task_id = uuid.uuid4().hex[:12]
    save_path = str(UPLOAD_DIR / f"{task_id}{ext}")
    file.save(save_path)
    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)

    uid = _get_uid()

    # Persist task to DB
    try:
        from services.task_service import TaskService
        TaskService.create_task(
            task_id=task_id,
            user_id=uid,
            filename=file.filename,
            file_size_mb=round(file_size_mb, 2),
            enable_diarization=enable_diarization,
            provider=provider,
            model=model,
        )
    except Exception as e:
        logger.warning(f"[Upload] DB create_task failed (non-fatal): {e}")

    # Background transcription
    t = threading.Thread(
        target=TranscriptionService.run_transcription,
        args=(task_id, save_path, base_url, api_key, model,
              max_minutes, max_mb, provider, uid, enable_diarization),
        daemon=True,
    )
    t.start()

    return success_response({"task_id": task_id, "file_size_mb": round(file_size_mb, 2)})


# ── Task Status ──

@transcription_bp.route("/<task_id>", methods=["GET"])
@jwt_required
def status(task_id):
    uid = _get_uid()

    # Check in-memory store first (for live progress)
    user_tasks = tasks.get(uid, {})
    task = user_tasks.get(task_id)
    if task:
        return success_response(task)

    # Fallback to DB
    try:
        from services.task_service import TaskService
        db_task = TaskService.get_task(task_id, uid)
        if db_task:
            return success_response(db_task)
    except Exception as e:
        logger.warning(f"[Status] DB get_task failed: {e}")

    return not_found("任务不存在")


# ── List Tasks ──

@transcription_bp.route("/", methods=["GET"])
@jwt_required
def list_tasks():
    uid = _get_uid()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search = request.args.get("search", "")

    # Merge: in-memory (live) + DB (persisted)
    # Start with DB results
    db_items = []
    db_total = 0
    try:
        from services.task_service import TaskService
        result = TaskService.list_tasks(uid, page, per_page, search)
        db_items = result["items"]
        db_total = result["total"]
    except Exception as e:
        logger.warning(f"[ListTasks] DB list_tasks failed: {e}")

    # Add in-memory tasks not yet in DB (status != done/error)
    user_tasks = tasks.get(uid, {})
    in_progress_items = []
    db_ids = {item["id"] for item in db_items}
    for tid, t in user_tasks.items():
        if tid not in db_ids:
            in_progress_items.append({
                "id": tid,
                "task_id": tid,
                "status": t.get("status", "unknown"),
                "transcript": t.get("transcript", "")[:200] if t.get("transcript") else "",
                "error": t.get("error", ""),
                "created_at": t.get("created_at", ""),
                "filename": t.get("file_name", ""),
                "file_name": t.get("file_name", ""),
                "provider": t.get("provider", ""),
            })

    # In-progress first, then DB results
    all_items = in_progress_items + db_items
    total = db_total + len(in_progress_items)

    return paginated_response(all_items, total, page, per_page)


# ── Delete Task ──

@transcription_bp.route("/<task_id>", methods=["DELETE"])
@jwt_required
def delete_task(task_id):
    uid = _get_uid()

    # Remove from in-memory
    user_tasks = tasks.get(uid, {})
    if task_id in user_tasks:
        del user_tasks[task_id]

    # Remove from DB
    try:
        from services.task_service import TaskService
        deleted = TaskService.delete_task(task_id, uid)
        if deleted:
            return success_response({"ok": True})
    except Exception as e:
        logger.warning(f"[Delete] DB delete_task failed: {e}")

    # Even if DB didn't have it, memory removal is fine
    return success_response({"ok": True})


# ── Update Speakers ──

@transcription_bp.route("/<task_id>/speakers", methods=["POST"])
@jwt_required
def update_speakers(task_id):
    uid = _get_uid()
    data = request.json or {}
    speaker_updates = data.get("speakers", [])

    if not speaker_updates:
        return bad_request("请提供要更新的说话人列表")

    # Update in-memory task
    user_tasks = tasks.get(uid, {})
    task = user_tasks.get(task_id)
    if task:
        transcript = task.get("transcript", "")
        speakers = task.get("speakers", [])
        for update in speaker_updates:
            label = update.get("label")
            new_name = update.get("name")
            if label and new_name:
                old_tag = f"【{label}】"
                new_tag = f"【{new_name}】"
                transcript = transcript.replace(old_tag, new_tag)
                for spk in speakers:
                    if spk.get("label") == label:
                        spk["matched_name"] = new_name
        task["transcript"] = transcript
        task["speakers"] = speakers

    # Persist to DB
    try:
        from services.task_service import TaskService
        TaskService.update_task_speakers(task_id, uid, speaker_updates)
    except Exception as e:
        logger.warning(f"[UpdateSpeakers] DB update failed: {e}")

    return success_response({"ok": True})


# ── Providers ──

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
    return success_response(available)


# ── Test Connection ──

@transcription_bp.route("/test-connection", methods=["POST"])
@jwt_required
def test_connection():
    data = request.json or {}
    provider = data.get("provider", "")
    base_url = data.get("base_url", "").strip()
    api_key = data.get("api_key", "").strip()
    model = data.get("model", "").strip()

    # For built-in providers, use server config
    builtin = BUILTIN_PROVIDERS.get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model = model or builtin["model"]
        api_key = _get_builtin_key(provider)
        if not api_key:
            return error_response("CONFIG_MISSING",
                                  f"服务端未配置 {builtin['api_key_env']}", 400)

    if not all([base_url, api_key, model]):
        return bad_request("请填写 Base URL、API Key 和 Model")

    try:
        from openai import OpenAI
        client = OpenAI(base_url=base_url, api_key=api_key)
        # Simple models list to verify connectivity
        client.models.list()
        return success_response({"ok": True, "message": "连接成功"})
    except Exception as e:
        return error_response("CONNECTION_FAILED", f"连接失败: {str(e)}", 400)
