from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import login_required, current_user
from pathlib import Path
from services.speaker_service import SpeakerService
from services.task_service import TaskService
from speaker import CLIPS_DIR

speaker_bp = Blueprint("speakers", __name__, url_prefix="/api/speakers")

@speaker_bp.route("/", methods=["GET"])
@login_required
def list_speakers():
    profiles = SpeakerService.get_user_profiles(current_user.id)
    return jsonify({"profiles": profiles})

@speaker_bp.route("/<int:profile_id>/name", methods=["POST"])
@login_required
def update_speaker_name(profile_id):
    data = request.json or {}
    name = data.get("name", "").strip()
    success, error = SpeakerService.update_name(profile_id, current_user.id, name)
    if not success:
        return jsonify({"error": error}), 400 if error else 404
    return jsonify({"ok": True, "name": name})

@speaker_bp.route("/<int:profile_id>", methods=["DELETE"])
@login_required
def delete_speaker(profile_id):
    success, error = SpeakerService.delete_profile(profile_id, current_user.id)
    if not success:
        return jsonify({"error": error}), 404
    return jsonify({"ok": True})

@speaker_bp.route("/merge", methods=["POST"])
@login_required
def merge_speakers():
    data = request.json or {}
    keep_id = data.get("keep_id")
    merge_id = data.get("merge_id")
    if not keep_id or not merge_id:
        return jsonify({"error": "请指定要合并的说话人"}), 400
    success, error = SpeakerService.merge_profiles(keep_id, merge_id, current_user.id)
    if not success:
        return jsonify({"error": error}), 404
    return jsonify({"ok": True})

@speaker_bp.route("/clips/<path:filename>", methods=["GET"])
@login_required
def serve_clip_direct(filename):
    safe_name = Path(filename).name
    clip_path = CLIPS_DIR / safe_name
    if not clip_path.exists():
        return jsonify({"error": "片段不存在"}), 404
    return send_from_directory(str(CLIPS_DIR), safe_name)

@speaker_bp.route("/<int:profile_id>/clips/<path:filename>", methods=["GET"])
@login_required
def serve_speaker_clip(profile_id, filename):
    # Verification of ownership could be added here if needed,
    # but SpeakerService.get_user_profiles already filters by user.
    # For simplicity, we just serve it if it exists in CLIPS_DIR.
    # But let's check profile ownership for better security.
    from speaker_db import get_profile
    profile = get_profile(profile_id)
    if not profile or profile["user_id"] != current_user.id:
        return jsonify({"error": "说话人不存在"}), 404

    safe_name = Path(filename).name
    clip_path = CLIPS_DIR / safe_name
    if not clip_path.exists():
        return jsonify({"error": "片段不存在"}), 404
    return send_from_directory(str(CLIPS_DIR), safe_name)

@speaker_bp.route("/task/<task_id>/update", methods=["POST"])
@login_required
def update_task_speakers(task_id):
    """
    Update speaker labels and names for a specific task.
    Request body: { "speakers": [ { "label": "说话人1", "name": "张三", "matched_profile_id": 123 }, ... ] }
    """
    data = request.json or {}
    speaker_updates = data.get("speakers", [])

    # Update the task record
    success = TaskService.update_task_speakers(task_id, current_user.id, speaker_updates)
    if not success:
        return jsonify({"error": "任务不存在或更新失败"}), 404

    # Optional: If user wants to save these to the library
    save_to_library = data.get("save_to_library", False)
    if save_to_library:
        task = TaskService.get_task(task_id, current_user.id)
        if task and "speakers" in task:
            SpeakerService.save_task_speakers(current_user.id, task["speakers"], speaker_updates)

    # Return updated task
    updated_task = TaskService.get_task(task_id, current_user.id)
    return jsonify(updated_task)

@speaker_bp.route("/save", methods=["POST"])
@login_required
def save_speakers_from_task():
    """Legacy endpoint for compatibility, can be merged into update_task_speakers."""
    data = request.json or {}
    task_id = data.get("task_id", "")
    speaker_updates = data.get("speakers", [])

    task = TaskService.get_task(task_id, current_user.id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    saved = SpeakerService.save_task_speakers(current_user.id, task.get("speakers", []), speaker_updates)

    # Also update task metadata and transcript
    TaskService.update_task_speakers(task_id, current_user.id, speaker_updates)

    updated_task = TaskService.get_task(task_id, current_user.id)
    return jsonify({
        "ok": True,
        "saved": saved,
        "transcript": updated_task.get("transcript"),
        "speakers": updated_task.get("speakers")
    })
