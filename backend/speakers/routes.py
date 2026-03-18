from flask import Blueprint, request, jsonify, send_from_directory, g
from pathlib import Path
from .service import SpeakerService
from .db import CLIPS_DIR, get_profile

# Mock jwt_required if not available from Track A
try:
    from backend.auth.routes import jwt_required
except ImportError:
    def jwt_required(f):
        return f

speaker_bp = Blueprint("speakers", __name__)

@speaker_bp.route("/", methods=["GET"])
@jwt_required
def list_speakers():
    uid = getattr(g, 'user_id', 0)
    cu = getattr(g, 'current_user', None)
    if cu and hasattr(cu, 'id'):
        uid = cu.id
    profiles = SpeakerService.get_user_profiles(uid)
    return jsonify({"profiles": profiles})

@speaker_bp.route("/<int:profile_id>/name", methods=["POST"])
@jwt_required
def update_speaker_name(profile_id):
    uid = getattr(g, 'user_id', 0)
    data = request.json or {}
    name = data.get("name", "").strip()
    success, error = SpeakerService.update_name(profile_id, uid, name)
    if not success:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": error}}), 400 if error else 404
    return jsonify({"data": {"ok": True, "name": name}})

@speaker_bp.route("/<int:profile_id>", methods=["DELETE"])
@jwt_required
def delete_speaker(profile_id):
    uid = getattr(g, 'user_id', 0)
    success, error = SpeakerService.delete_profile(profile_id, uid)
    if not success:
        return jsonify({"error": {"code": "NOT_FOUND", "message": error}}), 404
    return jsonify({"data": {"ok": True}})

@speaker_bp.route("/merge", methods=["POST"])
@jwt_required
def merge_speakers():
    uid = getattr(g, 'user_id', 0)
    data = request.json or {}
    keep_id = data.get("keep_id")
    merge_id = data.get("merge_id")
    if not keep_id or not merge_id:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "\u8bf7\u6307\u5b9a\u8981\u5408\u5e76\u7684\u8bf4\u8bdd\u4eba"}}), 400
    success, error = SpeakerService.merge_profiles(keep_id, merge_id, uid)
    if not success:
        return jsonify({"error": {"code": "NOT_FOUND", "message": error}}), 404
    return jsonify({"data": {"ok": True}})


@speaker_bp.route("/task/<task_id>/update", methods=["POST"])
@jwt_required
def update_task_speakers(task_id):
    """Update speaker names in an in-memory transcription task."""
    uid = getattr(g, 'user_id', 0)
    cu = getattr(g, 'current_user', None)
    if cu:
        uid = cu.id

    data = request.json or {}
    speakers = data.get("speakers", [])
    save_to_library = data.get("save_to_library", False)

    # Find the task - try in-memory first, but we must also read from DB
    from services.task_service import TaskService
    db_task = TaskService.get_task(task_id, uid)
    
    try:
        from backend.transcriptions.service import tasks as inmem_tasks
        user_tasks = inmem_tasks.get(uid, {})
        inmem_task = user_tasks.get(task_id)
    except Exception:
        inmem_task = None

    if not db_task and not inmem_task:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "任务不存在"}}), 404
        
    # Prefer in-memory if available and active, otherwise use db_task
    # But since historical tasks are often only in DB, we must use db_task's current state as baseline if inmem doesn't have it
    target_obj = inmem_task if inmem_task else db_task
    
    if target_obj is db_task:
        # DB task returns a dict, let's make sure it's mutable
        target_obj = dict(db_task)
        import json
        if isinstance(target_obj.get("speakers"), str):
            try: target_obj["speakers"] = json.loads(target_obj["speakers"])
            except: target_obj["speakers"] = []

    # Build old→new name mapping from the speakers list
    name_map = {}
    for sp in speakers:
        old_label = sp.get("label") or sp.get("original_label") or ""
        new_name = sp.get("name", "").strip()
        if old_label and new_name and old_label != new_name:
            name_map[old_label] = new_name

    # Apply name replacements in transcript text
    transcript = target_obj.get("transcript", "")
    if transcript and name_map:
        import re
        for old_name, new_name in name_map.items():
            # Replace 【old_name】 with 【new_name】
            transcript = transcript.replace(f"\u3010{old_name}\u3011", f"\u3010{new_name}\u3011")
        
        target_obj["transcript"] = transcript
        if inmem_task: inmem_task["transcript"] = transcript

    # Update the speakers list in the task
    updated_speakers = target_obj.get("speakers", [])
    if isinstance(updated_speakers, list):
        for sp_data in speakers:
            old_label = sp_data.get("label") or sp_data.get("original_label") or ""
            new_name = sp_data.get("name", "").strip()
            for existing in updated_speakers:
                if isinstance(existing, dict) and existing.get("label") == old_label:
                    existing["label"] = new_name
                    existing["name"] = new_name
                    if sp_data.get("matched_profile_id"):
                        existing["matched_profile_id"] = sp_data.get("matched_profile_id")
        target_obj["speakers"] = updated_speakers
        if inmem_task: inmem_task["speakers"] = updated_speakers

    # Persist the update to the SQLite DB
    try:
        TaskService.update_task(task_id, transcript=target_obj.get("transcript", ""), speakers=target_obj.get("speakers", []))
    except Exception as e:
        print(f"Failed to persist speaker rename to DB: {e}")

    # Optionally save to speaker library
    if save_to_library:
        for sp in speakers:
            new_name = sp.get("name", "").strip()
            profile_id = sp.get("matched_profile_id")
            if profile_id and new_name:
                SpeakerService.update_name(profile_id, uid, new_name)

    return jsonify({"data": {"ok": True, "transcript": target_obj.get("transcript", ""), "speakers": target_obj.get("speakers", [])}})

@speaker_bp.route("/clips/<path:filename>", methods=["GET"])
@jwt_required
def serve_clip_direct(filename):
    # Basic protection
    safe_name = Path(filename).name
    clip_path = CLIPS_DIR / safe_name
    if not clip_path.exists():
        return jsonify({"error": {"code": "NOT_FOUND", "message": "\u7247\u6bb5\u4e0d\u5b58\u5728"}}), 404
    return send_from_directory(str(CLIPS_DIR), safe_name)

@speaker_bp.route("/<int:profile_id>/clips/<path:filename>", methods=["GET"])
@jwt_required
def serve_speaker_clip(profile_id, filename):
    uid = getattr(g, 'user_id', 0)
    profile = get_profile(profile_id)
    if not profile or profile["user_id"] != uid:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "\u8bf4\u8bdd\u4eba\u4e0d\u5b58\u5728"}}), 404

    safe_name = Path(filename).name
    clip_path = CLIPS_DIR / safe_name
    if not clip_path.exists():
        return jsonify({"error": {"code": "NOT_FOUND", "message": "\u7247\u6bb5\u4e0d\u5b58\u5728"}}), 404
    return send_from_directory(str(CLIPS_DIR), safe_name)
