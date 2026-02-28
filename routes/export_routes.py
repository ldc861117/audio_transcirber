import io
from flask import Blueprint, request, send_file, jsonify
from flask_login import login_required, current_user
from services.export_service import ExportService
from services.task_service import TaskService

export_bp = Blueprint("export", __name__, url_prefix="/api/v1/export")
export_service = ExportService()

@export_bp.route("/<task_id>", methods=["GET", "POST"])
@login_required
def export_task(task_id):
    # GET: pull data from DB; POST: use provided data
    if request.method == "GET":
        task_data = TaskService.get_task(task_id, current_user.id)
        if not task_data:
            return jsonify({"error": "任务不存在"}), 404
        fmt = request.args.get("format", "txt").lower()
        transcript = task_data.get("transcript", "")
        speakers = task_data.get("speakers", [])
        metadata = {"filename": task_data.get("filename", f"export_{task_id}")}
    else:
        data = request.json or {}
        fmt = data.get("format", "txt").lower()
        transcript = data.get("transcript", "")
        speakers = data.get("speakers", [])
        metadata = data.get("metadata", {})
        if not metadata.get("filename"):
            metadata["filename"] = data.get("filename", f"export_{task_id}")

    filename = metadata["filename"]

    try:
        if fmt == "srt":
            content = export_service.export_srt(transcript, speakers)
            return send_file(
                io.BytesIO(content.encode("utf-8")),
                mimetype="text/plain",
                as_attachment=True,
                download_name=f"{filename}.srt"
            )
        elif fmt == "docx":
            content = export_service.export_word(transcript, metadata, speakers)
            return send_file(
                io.BytesIO(content),
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                as_attachment=True,
                download_name=f"{filename}.docx"
            )
        elif fmt == "pdf":
            content = export_service.export_pdf(transcript, metadata, speakers)
            return send_file(
                io.BytesIO(content),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"{filename}.pdf"
            )
        elif fmt == "txt":
            return send_file(
                io.BytesIO(transcript.encode("utf-8")),
                mimetype="text/plain",
                as_attachment=True,
                download_name=f"{filename}.txt"
            )
        elif fmt == "md":
            return send_file(
                io.BytesIO(transcript.encode("utf-8")),
                mimetype="text/markdown",
                as_attachment=True,
                download_name=f"{filename}.md"
            )
        else:
            return jsonify({"error": f"Unsupported format: {fmt}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
