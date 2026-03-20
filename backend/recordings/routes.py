import threading
from flask import Blueprint, request, jsonify, g

from backend.auth.decorators import jwt_required
from .service import RecordingSession

recordings_bp = Blueprint('recordings', __name__)


@recordings_bp.route("/start", methods=["POST"])
@jwt_required
def start_session():
    """Create a new recording session."""
    uid = g.current_user.id
    session = RecordingSession(user_id=uid)

    # Clean up old stale sessions in background
    threading.Thread(
        target=RecordingSession.cleanup_stale_sessions,
        args=(uid,),
        daemon=True,
    ).start()

    return jsonify({
        "data": {
            "session_id": session.session_id,
        }
    }), 201


@recordings_bp.route("/<session_id>/chunk", methods=["POST"])
@jwt_required
def append_chunk(session_id):
    """Append an audio chunk to an existing recording session."""
    uid = g.current_user.id

    # Verify session exists
    session_dir = RecordingSession.get_session_dir(uid, session_id)
    if not session_dir:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Recording session not found"}}), 404

    # Accept chunk from form data
    chunk_file = request.files.get("chunk")
    if not chunk_file:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing chunk data"}}), 400

    session = RecordingSession(user_id=uid, session_id=session_id)
    chunk_data = chunk_file.read()

    if len(chunk_data) == 0:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Empty chunk"}}), 400

    result = session.save_chunk(chunk_data)

    return jsonify({"data": result}), 200


@recordings_bp.route("/<session_id>/finalize", methods=["POST"])
@jwt_required
def finalize_session(session_id):
    """Finalize recording: concat chunks and optionally start transcription."""
    uid = g.current_user.id

    session_dir = RecordingSession.get_session_dir(uid, session_id)
    if not session_dir:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Recording session not found"}}), 404

    session = RecordingSession(user_id=uid, session_id=session_id)

    try:
        result = session.finalize()
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400
    except RuntimeError as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500

    # Auto-trigger transcription with Gemini provider
    auto_transcribe = request.json.get("auto_transcribe", True) if request.is_json else True

    task_id = None
    if auto_transcribe:
        task_id = _start_transcription(uid, result["file_path"])

    result["task_id"] = task_id
    return jsonify({"data": result}), 200


def _start_transcription(user_id: int, file_path: str) -> str | None:
    """Trigger transcription on the finalized recording file."""
    try:
        import uuid
        from backend.transcriptions.service import TranscriptionService
        from backend.transcriptions.gemini_provider import BUILTIN_PROVIDERS, _get_builtin_key
        from backend.transcriptions.audio_utils import DEFAULT_MAX_CHUNK_MINUTES, DEFAULT_MAX_CHUNK_MB

        builtin = BUILTIN_PROVIDERS.get("gemini")
        if not builtin:
            return None

        api_key = _get_builtin_key("gemini")
        if not api_key:
            return None

        task_id = uuid.uuid4().hex[:12]

        t = threading.Thread(
            target=TranscriptionService.run_transcription,
            args=(
                task_id, file_path,
                builtin["base_url"], api_key, builtin["model"],
                DEFAULT_MAX_CHUNK_MINUTES, DEFAULT_MAX_CHUNK_MB,
                "gemini", user_id, False,
            ),
            daemon=True,
        )
        t.start()
        return task_id

    except Exception as e:
        print(f"⚠️ Auto-transcription trigger failed: {e}")
        return None
