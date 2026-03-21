from flask import Blueprint, request, jsonify, send_from_directory, g
from pathlib import Path
from .service import SpeakerService
from .db import CLIPS_DIR, get_profile
from backend.auth.decorators import jwt_required

speaker_bp = Blueprint("speakers", __name__)

@speaker_bp.route("/", methods=["GET"])
@jwt_required
def list_speakers():
    uid = g.current_user.id
    profiles = SpeakerService.get_user_profiles(uid)
    return jsonify({"data": profiles})

@speaker_bp.route("/<int:profile_id>/name", methods=["POST"])
@jwt_required
def update_speaker_name(profile_id):
    uid = g.current_user.id
    data = request.json or {}
    name = data.get("name", "").strip()
    success, error = SpeakerService.update_name(profile_id, uid, name)
    if not success:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": error}}), 400 if error else 404
    return jsonify({"data": {"ok": True, "name": name}})

@speaker_bp.route("/<int:profile_id>", methods=["DELETE"])
@jwt_required
def delete_speaker(profile_id):
    uid = g.current_user.id
    success, error = SpeakerService.delete_profile(profile_id, uid)
    if not success:
        return jsonify({"error": {"code": "NOT_FOUND", "message": error}}), 404
    return jsonify({"data": {"ok": True}})

@speaker_bp.route("/merge", methods=["POST"])
@jwt_required
def merge_speakers():
    uid = g.current_user.id
    data = request.json or {}
    keep_id = data.get("keep_id")
    merge_id = data.get("merge_id")
    if not keep_id or not merge_id:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "\u8bf7\u6307\u5b9a\u8981\u5408\u5e76\u7684\u8bf4\u8bdd\u4eba"}}), 400
    success, error = SpeakerService.merge_profiles(keep_id, merge_id, uid)
    if not success:
        return jsonify({"error": {"code": "NOT_FOUND", "message": error}}), 404
    return jsonify({"data": {"ok": True}})

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
    uid = g.current_user.id
    profile = get_profile(profile_id)
    if not profile or profile["user_id"] != uid:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "\u8bf4\u8bdd\u4eba\u4e0d\u5b58\u5728"}}), 404

    safe_name = Path(filename).name
    clip_path = CLIPS_DIR / safe_name
    if not clip_path.exists():
        return jsonify({"error": {"code": "NOT_FOUND", "message": "\u7247\u6bb5\u4e0d\u5b58\u5728"}}), 404
    return send_from_directory(str(CLIPS_DIR), safe_name)
