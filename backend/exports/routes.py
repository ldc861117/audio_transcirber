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


def _get_export_uid():
    """Get user ID for export, same logic as transcription routes."""
    cu = getattr(g, 'current_user', None)
    return cu.id if cu else getattr(g, 'user_id', 0)


@export_bp.route("/<task_id>", methods=["GET", "POST"])
@jwt_required
def export_task(task_id):
    uid = _get_export_uid()
    
    # GET: pull data from in-memory tasks or legacy DB
    if request.method == "GET":
        task_data = None
        
        # Try in-memory tasks first (V2 backend)
        try:
            from backend.transcriptions.service import tasks as inmem_tasks
            user_tasks = inmem_tasks.get(uid, {})
            t = user_tasks.get(task_id)
            if t and t.get("transcript"):
                task_data = t
        except Exception:
            pass
        
        # Fallback: check legacy DB
        if not task_data:
            try:
                from services.task_service import TaskService
                # Try with current uid
                legacy = TaskService.get_task(task_id, uid)
                if not legacy:
                    # Try with legacy uid
                    cu = getattr(g, 'current_user', None)
                    if cu:
                        import sqlite3, os
                        legacy_db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'users.db')
                        if os.path.exists(legacy_db):
                            conn = sqlite3.connect(legacy_db)
                            row = conn.execute("SELECT id FROM users WHERE username=?", (cu.username,)).fetchone()
                            conn.close()
                            if row:
                                legacy = TaskService.get_task(task_id, row[0])
                if legacy:
                    task_data = legacy
            except Exception:
                pass
        
        if not task_data:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "任务不存在"}}), 404
            
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
