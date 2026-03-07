import io
from flask import Blueprint, request, send_file, jsonify, g
from .service import ExportService

# Mock jwt_required if not available from Track A
try:
    from backend.auth.routes import jwt_required
except ImportError:
    def jwt_required(f):
        return f

export_bp = Blueprint("export", __name__)
export_service = ExportService()

@export_bp.route("/<task_id>", methods=["GET", "POST"])
@jwt_required
def export_task(task_id):
    uid = getattr(g, 'user_id', 0)
    
    # GET: pull data from DB; POST: use provided data
    if request.method == "GET":
        # from services.task_service import TaskService
        # task_data = TaskService.get_task(task_id, uid)
        task_data = None # Mock for now
        
        if not task_data:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "\u4efb\u52a1\u4e0d\u5b58\u5728"}}), 404
            
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
