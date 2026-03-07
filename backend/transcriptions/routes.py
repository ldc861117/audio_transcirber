import uuid
import os
import threading
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
    uid = getattr(g, 'user_id', 0)

    # ── [NEW] Quota Check (Track B) ──
    # try:
    #     from backend.subscriptions.service import QuotaService
    #     QuotaService.check_quota(uid, file_size_mb)
    # except QuotaExceededError:
    #     return jsonify({"error": {"code": "QUOTA_EXCEEDED", "message": "\u914d\u984d\u4e0d\u8db3"}}), 403

    # ── [NEW] Feature Permission Check (Track B) ──
    # if enable_diarization:
    #     try:
    #         from backend.subscriptions.service import PlanService
    #         PlanService.check_feature(uid, "diarization")
    #     except FeatureDeniedError:
    #         return jsonify({"error": {"code": "INSUFFICIENT_PLAN", "message": "\u8be5\u529f\u80fd\u9700\u8981\u66f4\u9ad8\u7248\u672c"}}), 403

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
    uid = getattr(g, 'user_id', 0)
    user_tasks = tasks.get(uid, {})
    task = user_tasks.get(task_id)
    if task:
        return jsonify({"data": task})
    
    # Fallback to database
    # db_task = TaskService.get_task(task_id, uid)
    # if db_task:
    #     return jsonify({"data": db_task})
    
    return jsonify({"error": {"code": "NOT_FOUND", "message": "\u4efb\u52a1\u4e0d\u5b58\u5728"}}), 404

@transcription_bp.route("/", methods=["GET"])
@jwt_required
def list_tasks():
    # Implementation for listing tasks with pagination
    return jsonify({"data": [], "meta": {"total": 0, "page": 1, "per_page": 20, "total_pages": 0}})

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
