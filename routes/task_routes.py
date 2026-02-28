"""
Task routes module for Audio Transcriber.
Defines API endpoints for managing transcription tasks.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from services.task_service import TaskService

task_bp = Blueprint("tasks", __name__, url_prefix="/api/v1/transcriptions")


@task_bp.route("/", methods=["GET"])
@login_required
def list_tasks():
    """Get a list of transcription tasks for the current user."""
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        search = request.args.get("search", "") or request.args.get("q", "")
        
        result = TaskService.list_tasks(
            user_id=current_user.id,
            page=page,
            per_page=per_page,
            search=search
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@task_bp.route("/<task_id>", methods=["GET"])
@login_required
def get_task(task_id):
    """Get details of a specific transcription task."""
    task = TaskService.get_task(task_id, current_user.id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task)


@task_bp.route("/<task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    """Delete a specific transcription task."""
    success = TaskService.delete_task(task_id, current_user.id)
    if not success:
        return jsonify({"error": "任务不存在或无权删除"}), 404
    return jsonify({"ok": True})
