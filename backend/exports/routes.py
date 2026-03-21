import io
import logging
from flask import Blueprint, request, send_file, jsonify, g
from .service import ExportService
from backend.auth.decorators import jwt_required
from backend.utils.responses import not_found

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)
export_service = ExportService()

@export_bp.route("/<task_id>", methods=["GET", "POST"])
@jwt_required
def export_task(task_id):
    uid = g.current_user.id if getattr(g, 'current_user', None) else 0
    
    # GET: pull data from DB; POST: use provided data
    if request.method == "GET":
        task_data = None
        try:
            from backend.transcriptions.task_service import TaskService
            task_data = TaskService.get_task(task_id, uid)
        except Exception as e:
            logger.warning(f"[Export] DB get_task failed: {e}")
        
        if not task_data:
            return not_found("任务不存在")
            
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
            return jsonify({"error": {"code": "BAD_REQUEST", "message": f"Unsupported format: {fmt}"}}), 400

    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500
