"""
Audio Transcription App — 音频自动切分与转写
Flask backend: receives audio files, splits them with pydub,
transcribes each chunk via an OpenAI-compatible Gemini API, and
merges results.  Supports speaker diarization and voiceprint matching.
"""

import os
import uuid
import base64
import tempfile
import threading
import traceback
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
from flask_login import login_user, logout_user, login_required, current_user
import sqlite3 as _sqlite3
from pydub import AudioSegment
from openai import OpenAI
try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

from auth import setup_auth, User
import speaker_db
from speaker import (
    parse_diarization_response, process_speakers,
    merge_cross_chunk_speakers, speaker_result_to_dict,
    CLIPS_DIR,
)

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app, origins=["http://localhost:5099", "http://localhost:3000"])
setup_auth(app)

# ── Phase 1 Blueprints ────────────────────────────────────
from routes.task_routes import task_bp
from routes.plan_routes import plan_bp
from routes.export_routes import export_bp
from routes.recording_routes import recording_bp
from routes.speaker_routes import speaker_bp
from services.task_service import TaskService

app.register_blueprint(task_bp)
app.register_blueprint(plan_bp)
app.register_blueprint(export_bp)
app.register_blueprint(recording_bp)
app.register_blueprint(speaker_bp)

UPLOAD_DIR = Path(tempfile.gettempdir()) / "audio_transcriber_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# All audio formats supported by ffmpeg / pydub
SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a",
    ".wma", ".aiff", ".aif", ".opus", ".amr", ".ape",
    ".ac3", ".webm", ".caf", ".spx", ".oga", ".wv",
    ".mp4", ".mov", ".mkv",  # video files with audio track
}

# In-memory task store  {user_id: {task_id: {...}}}
# Scoped per user so each user only sees their own tasks.
tasks: dict[int, dict[str, dict]] = {}

# ── defaults (overridable per-request) ──────────────────────────
DEFAULT_MAX_CHUNK_MINUTES = 10       # minutes per chunk
DEFAULT_MAX_CHUNK_MB      = 20       # MB per chunk (safe for base64 inline)

# Load optional defaults from environment (for Quick Start / Test Mode)
DEFAULT_BASE_URL = os.environ.get("custom_openai_baseurl", "")
DEFAULT_API_KEY  = os.environ.get("custom_openai_apikey", "")
DEFAULT_MODEL    = os.environ.get("custom_openai_model", "")
TEST_MODE        = os.environ.get("test_mode", "false").lower() == "true"
SERVER_ENV_SENTINEL = "(server-env)"

# ── Built-in provider configs (API keys from env, rest hardcoded) ────
BUILTIN_PROVIDERS = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-3-flash-preview",
        "api_key_env": "GEMINI_API_KEY",
    },
}

def _get_builtin_key(provider_name: str) -> str:
    """Return the API key for a built-in provider, or empty string."""
    info = BUILTIN_PROVIDERS.get(provider_name, {})
    env_var = info.get("api_key_env", "")
    return os.environ.get(env_var, "") if env_var else ""

DEMO_AUDIO_DIR = Path(__file__).resolve().parent / "demo_audio"
DEMO_AUDIO_DIR.mkdir(exist_ok=True)


# ================================================================
#  Utilities
# ================================================================

def split_audio(filepath: str, max_minutes: int, max_mb: int, preferred_format: str = "mp3") -> list[str]:
    """
    Split an audio file by duration AND file-size constraints.
    Returns a list of temporary file paths for each chunk.
    """
    audio = AudioSegment.from_file(filepath)
    fmt = preferred_format if preferred_format in ["mp3", "m4a"] else "mp3"

    chunk_ms = max_minutes * 60 * 1000
    chunks_by_time: list[AudioSegment] = []

    # First pass: split by time
    for start in range(0, len(audio), chunk_ms):
        chunks_by_time.append(audio[start:start + chunk_ms])

    # Second pass: further split any chunk that exceeds max_mb
    final_chunks: list[AudioSegment] = []
    for chunk in chunks_by_time:
        tmp = tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False)
        chunk.export(tmp.name, format=fmt)
        tmp.close()
        size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
        os.unlink(tmp.name)

        if size_mb <= max_mb:
            final_chunks.append(chunk)
        else:
            # Binary-split until every piece fits
            sub_chunks = _binary_split(chunk, fmt, max_mb)
            final_chunks.extend(sub_chunks)

    # Export final chunks
    paths: list[str] = []
    for i, chunk in enumerate(final_chunks):
        out = UPLOAD_DIR / f"{uuid.uuid4().hex}_{i}.{fmt}"
        chunk.export(str(out), format=fmt)
        paths.append(str(out))
    return paths


def _binary_split(segment: AudioSegment, fmt: str, max_mb: int) -> list[AudioSegment]:
    """Recursively halve a segment until each piece is <= max_mb."""
    tmp = tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False)
    segment.export(tmp.name, format=fmt)
    tmp.close()
    size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
    os.unlink(tmp.name)

    if size_mb <= max_mb:
        return [segment]
    mid = len(segment) // 2
    return _binary_split(segment[:mid], fmt, max_mb) + \
           _binary_split(segment[mid:], fmt, max_mb)


# ── Prompt constants ───────────────────────────────────────────
_SYSTEM_PROMPT = (
    "\u4f60\u662f\u4e00\u4f4d\u62e5\u6709 20 \u5e74\u7ecf\u9a8c\u7684\u4e13\u4e1a\u4f1a\u8bae\u901f\u8bb0\u5458\u548c\u7eaa\u8981\u4e13\u5bb6\u3002"
    "\u4f60\u7684\u4efb\u52a1\u662f\u5c06\u97f3\u9891\u5185\u5bb9\u8f6c\u5316\u4e3a\u201c\u667a\u80fd\u9010\u5b57\u7a3f\u201d\uff08Intelligent Verbatim\uff09\u3002"
    "\u6838\u5fc3\u539f\u5219\uff1a\u4fdd\u6301\u5185\u5bb9\u7684\u5b8c\u6574\u6027\u548c\u51c6\u786e\u6027\uff0c\u540c\u65f6\u63d0\u5347\u9605\u8bfb\u4f53\u9a8c\u3002"
    "\u91cd\u8981\uff1a\u8bf7\u59cb\u7ec8\u4f7f\u7528\u7b80\u4f53\u4e2d\u6587\uff08Simplified Chinese\uff09\u8f93\u51fa\uff0c\u4e0d\u8981\u4f7f\u7528\u7e41\u4f53\u4e2d\u6587\u3002"
)

_USER_PROMPT_STANDARD = (
    "\u8bf7\u5bf9\u4ee5\u4e0b\u97f3\u9891\u8fdb\u884c\u4e13\u4e1a\u8f6c\u5199\u3002\u9075\u5faa\u4ee5\u4e0b\u4e1a\u754c\u6807\u51c6\u89c4\u8303\uff1a\n\n"
    "1. **\u667a\u80fd\u51c0\u5316**\uff1a\n"
    "   - \u5254\u9664\u53e3\u8bed\u5e9f\u8bdd\uff08\u5982\u201c\u90a3\u4e2a\u201d\u3001\u201c\u5462\u201d\u3001\u201c\u55ef\u201d\u3001\u201c\u5c31\u662f\u8bf4\u201d\u7b49\uff09\uff0c\u9664\u975e\u8868\u8fbe\u8fdf\u7591\u6216\u5f3a\u8c03\uff1b\n"
    "   - \u4fee\u6b63\u660e\u663e\u7684\u53e3\u8bef\u548c\u91cd\u590d\uff08\u5982\u201c\u6211...\u6211\u4eec\u8ba4\u4e3a\u201d -> \u201c\u6211\u4eec\u8ba4\u4e3a\u201d\uff09\uff1b\n"
    "   - \u4fdd\u6301\u539f\u672c\u7684\u8bed\u5e8f\u548c\u903b\u8f91\uff0c\u4e0d\u8981\u968f\u610f\u6539\u5199\u5185\u5bb9\u3002\n\n"
    "2. **\u683c\u5f0f\u89c4\u8303**\uff1a\n"
    "   - **\u8bf4\u8bdd\u4eba\u6807\u8bb0**\uff1a\u6839\u636e\u58f0\u7eb9\u548c\u4e0a\u4e0b\u6587\u533a\u5206\u8bf4\u8bdd\u4eba\uff0c\u4f7f\u7528\u3010\u8bf4\u8bdd\u4eba1\u3011\u3001\u3010\u8bf4\u8bdd\u4eba2\u3011\u6216\u5177\u4f53\u79f0\u8c13\uff08\u5982\u3010\u4e3b\u6301\u4eba\u3011\u3001\u3010\u7ecf\u7406\u3011\uff09\u6807\u8bb0\uff1b\n"
    "   - **\u6bb5\u843d\u5206\u660e**\uff1a\u4e0d\u540c\u8bf4\u8bdd\u4eba\u5fc5\u987b\u6362\u884c\u3002\u957f\u6bb5\u72ec\u767d\u8bf7\u6839\u636e\u903b\u8f91\u8bed\u4e49\u5408\u7406\u5206\u6bb5\uff1b\n"
    "   - **\u6807\u70b9\u4e13\u4e1a**\uff1a\u4f7f\u7528\u89c4\u8303\u7684\u4e2d\u6587\u5168\u89d2\u6807\u70b9\u3002\u8bed\u6c14\u5f3a\u70c8\u7684\u7528\u611f\u53f9\u53f7\uff0c\u7591\u95ee\u7528\u95ee\u53f7\uff0c\u5e76\u5217\u7528\u987f\u53f7\u3002\n\n"
    "3. **\u5173\u952e\u5185\u5bb9\u7a81\u51fa**\uff1a\n"
    "   - \u5bf9\u4e8e**\u5173\u952e\u6570\u636e**\uff08\u91d1\u989d\u3001\u65f6\u95f4\u3001\u6570\u91cf\uff09\u3001**\u4e13\u6709\u540d\u8bcd**\uff08\u9879\u76ee\u540d\u3001\u90e8\u95e8\u540d\u3001\u6280\u672f\u672f\u8bed\uff09\uff0c\u8bf7\u786e\u4fdd\u51c6\u786e\u65e0\u8bef\uff1b\n"
    "   - \u5982\u9047\u51b3\u7b56\u6027\u7ed3\u8bba\u6216\u5f85\u529e\u4e8b\u9879\uff0c\u4fdd\u6301\u539f\u8bdd\uff0c\u4e0d\u8981\u9057\u6f0f\u3002\n\n"
    "4. **\u6df7\u5408\u8bed\u8a00\u5904\u7406**\uff1a\n"
    "   - \u4e2d\u82f1\u6587\u6df7\u6742\u65f6\uff0c\u82f1\u6587\u5355\u8bcd\u524d\u540e\u4fdd\u7559\u7a7a\u683c\uff08\u5982\u201c\u4f7f\u7528 AI \u6280\u672f\u201d\uff09\u3002\n"
    "   - \u4ec5\u8f93\u51fa\u8f6c\u5199\u6b63\u6587\uff0c\u4e0d\u8981\u5305\u542b\u201c\u597d\u7684\u201d\u3001\u201c\u4ee5\u4e0b\u662f\u8f6c\u5199\u201d\u7b49\u65e0\u5173\u56de\u590d\u3002"
)

_USER_PROMPT_DIARIZATION = (
    "\u8bf7\u5bf9\u4ee5\u4e0b\u97f3\u9891\u8fdb\u884c\u4e13\u4e1a\u8f6c\u5199\uff0c\u5e76\u8f93\u51fa\u7ed3\u6784\u5316 JSON \u683c\u5f0f\u4ee5\u652f\u6301\u8bf4\u8bdd\u4eba\u8bc6\u522b\u3002\n\n"
    "**\u8f93\u51fa\u8981\u6c42**\uff1a\u4ec5\u8f93\u51fa\u4e00\u4e2a JSON \u5bf9\u8c61\uff0c\u4e0d\u8981\u5305\u542b\u4efb\u4f55\u5176\u4ed6\u6587\u5b57\uff1a\n"
    '{\"segments\": [\n'
    '  {\"speaker\": \"\u8bf4\u8bdd\u4eba1\", \"start\": 0.0, \"end\": 15.3, \"text\": \"\u8f6c\u5199\u5185\u5bb9...\"},\n'
    '  {\"speaker\": \"\u8bf4\u8bdd\u4eba2\", \"start\": 15.3, \"end\": 28.7, \"text\": \"\u8f6c\u5199\u5185\u5bb9...\"}\n'
    ']}\n\n'
    "**\u8f6c\u5199\u89c4\u8303**\uff1a\n"
    "1. **\u8bf4\u8bdd\u4eba\u533a\u5206**\uff1a\u6839\u636e\u58f0\u7eb9\u548c\u4e0a\u4e0b\u6587\u533a\u5206\u4e0d\u540c\u8bf4\u8bdd\u4eba\uff0c\u4f7f\u7528 \"\u8bf4\u8bdd\u4eba1\"\u3001\"\u8bf4\u8bdd\u4eba2\" \u7b49\u6807\u8bb0\uff1b\n"
    "2. **\u65f6\u95f4\u6233**\uff1astart \u548c end \u662f\u8be5\u6bb5\u53d1\u8a00\u5728\u97f3\u9891\u4e2d\u7684\u8fd1\u4f3c\u79d2\u6570\uff0c\u5c3d\u91cf\u51c6\u786e\uff1b\n"
    "3. **\u667a\u80fd\u51c0\u5316**\uff1a\u5254\u9664\u53e3\u8bed\u5e9f\u8bdd\uff0c\u4fee\u6b63\u53e3\u8bef\u548c\u91cd\u590d\uff0c\u4fdd\u6301\u539f\u610f\uff1b\n"
    "4. **\u4fdd\u6301\u5b8c\u6574**\uff1a\u4e0d\u8981\u9057\u6f0f\u4efb\u4f55\u5b9e\u8d28\u5185\u5bb9\uff1b\n"
    "5. **\u7b80\u4f53\u4e2d\u6587**\uff1a\u59cb\u7ec8\u4f7f\u7528\u7b80\u4f53\u4e2d\u6587\u8f93\u51fa\u3002"
)


def transcribe_chunk(chunk_path: str, client, model: str, provider: str = "openai",
                     enable_diarization: bool = False) -> str:
    """Send a single audio chunk to the appropriate API and return text."""
    if provider == "zhipu" and ZhipuAI and isinstance(client, ZhipuAI) and ("asr" in model.lower() or model == "glm-asr-2512"):
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(model=model, file=f)
        return response.text

    if provider == "modelscope":
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model, file=f, response_format="text"
            )
        return response if isinstance(response, str) else response.text

    # Default: OpenAI-compatible Multimodal Chat completion
    mime = "audio/mpeg" if chunk_path.endswith(".mp3") else "audio/mp4"
    with open(chunk_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    user_prompt = _USER_PROMPT_DIARIZATION if enable_diarization else _USER_PROMPT_STANDARD

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }
        ],
        "max_tokens": 8192,
    }

    # Special: Zhipu Thinking parameter
    if provider == "zhipu" and "glm-4.6v" in model:
        kwargs["extra_body"] = {"thinking": True}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()


def run_transcription(task_id: str, filepath: str,
                      base_url: str, api_key: str, model: str,
                      max_minutes: int, max_mb: int, provider: str = "openai",
                      user_id: int = 0, enable_diarization: bool = False):
    """Background worker: split -> transcribe -> (optional) diarize -> merge."""
    task = tasks[user_id][task_id]
    original_filepath = filepath
    try:
        # -- 1. Split ------------------------------------------------
        task["status"] = "splitting"
        pref_fmt = "m4a" if provider == "zhipu" else "mp3"
        chunks = split_audio(filepath, max_minutes, max_mb, preferred_format=pref_fmt)
        task["total_chunks"] = len(chunks)
        task["status"] = "transcribing"

        # -- 2. Transcribe each chunk --------------------------------
        if provider == "zhipu" and ZhipuAI:
            client = ZhipuAI(api_key=api_key)
        else:
            client = OpenAI(base_url=base_url, api_key=api_key)

        results: list[str] = []
        chunk_paths_kept: list[str] = []  # keep for diarization

        for i, chunk_path in enumerate(chunks):
            task["current_chunk"] = i + 1
            task["completed_chunks"] = i
            try:
                text = transcribe_chunk(
                    chunk_path, client, model, provider=provider,
                    enable_diarization=enable_diarization,
                )
                results.append(text)
                task["chunk_results"].append({
                    "index": i + 1,
                    "status": "done",
                    "text": text,
                })
            except Exception as e:
                err_msg = str(e)
                results.append(f"[\u7247\u6bb5 {i+1} \u8f6c\u5199\u5931\u8d25: {err_msg}]")
                task["chunk_results"].append({
                    "index": i + 1,
                    "status": "error",
                    "text": err_msg,
                })
            finally:
                task["completed_chunks"] = i + 1
                if enable_diarization:
                    chunk_paths_kept.append(chunk_path)
                else:
                    try:
                        os.unlink(chunk_path)
                    except OSError:
                        pass

        # -- 3. Assemble transcript --------------------------------
        if enable_diarization:
            all_segments_text = []
            for r in results:
                segments = parse_diarization_response(r)
                if segments:
                    for seg in segments:
                        all_segments_text.append(
                            f"\u3010{seg.speaker_label}\u3011{seg.text}"
                        )
                else:
                    all_segments_text.append(r)
            task["transcript"] = "\n\n".join(all_segments_text)
        else:
            task["transcript"] = "\n\n".join(results)

        # -- 4. Speaker diarization (optional) -----------------------
        if enable_diarization:
            task["status"] = "diarizing"
            try:
                chunk_speaker_results = []
                for idx, (chunk_path, text) in enumerate(zip(chunk_paths_kept, results)):
                    segments = parse_diarization_response(text)
                    print(f"[Diarize] Chunk {idx}: parsed {len(segments)} segments")
                    for seg in segments:
                        print(f"  - {seg.speaker_label}: {seg.start_time:.1f}-{seg.end_time:.1f}s ({len(seg.text)} chars)")
                    if segments:
                        speaker_results = process_speakers(
                            chunk_path, segments, user_id
                        )
                        print(f"[Diarize] Chunk {idx}: {len(speaker_results)} speakers processed")
                        chunk_speaker_results.append(speaker_results)

                if chunk_speaker_results:
                    merged_speakers = merge_cross_chunk_speakers(chunk_speaker_results)
                    print(f"[Diarize] After merge: {len(merged_speakers)} speakers")
                    for sp in merged_speakers:
                        print(f"  - {sp.label}: {sp.total_duration:.1f}s, {len(sp.clip_paths)} clips, embedding={'yes' if sp.embedding is not None else 'no'}")
                    task["speakers"] = [
                        speaker_result_to_dict(s) for s in merged_speakers
                    ]
                    # Auto-replace matched speaker labels in transcript
                    transcript = task.get("transcript", "")
                    for sp_dict in task["speakers"]:
                        if sp_dict.get("matched_name"):
                            old_tag = f"\u3010{sp_dict['label']}\u3011"
                            new_tag = f"\u3010{sp_dict['matched_name']}\u3011"
                            transcript = transcript.replace(old_tag, new_tag)
                    task["transcript"] = transcript
                else:
                    task["speakers"] = []

            except Exception as e:
                import traceback as _tb
                print(f"\u26a0\ufe0f Diarization failed: {e}")
                _tb.print_exc()
                task["speakers"] = []
                task["diarization_error"] = str(e)
            finally:
                for cp in chunk_paths_kept:
                    try:
                        os.unlink(cp)
                    except OSError:
                        pass

        task["status"] = "done"

        # ── Persist final result to SQLite ──
        try:
            TaskService.update_task(task_id,
                status="done",
                transcript=task.get("transcript", ""),
                speakers=task.get("speakers", []),
                chunk_count=task.get("total_chunks", 0),
                error="",
            )
        except Exception as db_err:
            print(f"⚠️ DB persist failed: {db_err}")

    except Exception:
        task["status"] = "error"
        task["error"] = traceback.format_exc()
        try:
            TaskService.update_task(task_id, status="error", error=task["error"])
        except Exception:
            pass
    finally:
        try:
            os.unlink(original_filepath)
        except OSError:
            pass


# ================================================================
#  Routes
# ================================================================

# ================================================================
#  Auth Routes
# ================================================================

@app.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect("/")
    return send_from_directory("static", "login.html")


@app.route("/register")
def register_page():
    if current_user.is_authenticated:
        return redirect("/")
    return send_from_directory("static", "register.html")


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "\u8bf7\u586b\u5199\u7528\u6237\u540d\u548c\u5bc6\u7801"}), 400
    if len(username) < 2 or len(username) > 32:
        return jsonify({"error": "\u7528\u6237\u540d\u957f\u5ea6\u9700\u5728 2-32 \u4e2a\u5b57\u7b26\u4e4b\u95f4"}), 400
    if len(password) < 6:
        return jsonify({"error": "\u5bc6\u7801\u957f\u5ea6\u81f3\u5c11 6 \u4e2a\u5b57\u7b26"}), 400
    if User.username_exists(username):
        return jsonify({"error": "\u7528\u6237\u540d\u5df2\u88ab\u6ce8\u518c"}), 409

    try:
        user = User.create(username, password)
    except _sqlite3.IntegrityError:
        return jsonify({"error": "\u7528\u6237\u540d\u5df2\u88ab\u6ce8\u518c"}), 409

    login_user(user, remember=True)
    return jsonify({"ok": True, "username": user.username})


@app.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"error": "\u8bf7\u586b\u5199\u7528\u6237\u540d\u548c\u5bc6\u7801"}), 400

    user = User.authenticate(username, password)
    if not user:
        return jsonify({"error": "\u7528\u6237\u540d\u6216\u5bc6\u7801\u9519\u8bef"}), 401

    login_user(user, remember=True)
    return jsonify({"ok": True, "username": user.username})


@app.route("/api/auth/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"ok": True})


@app.route("/api/auth/me")
@login_required
def api_me():
    return jsonify({"username": current_user.username})


# ================================================================
#  App Routes
# ================================================================

@app.route("/")
@app.route("/transcribe")
@app.route("/history")
@app.route("/speakers")
@app.route("/settings")
@login_required
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "\u672a\u6536\u5230\u97f3\u9891\u6587\u4ef6"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return jsonify({"error": f"\u4e0d\u652f\u6301\u7684\u683c\u5f0f {ext}\uff0c\u652f\u6301: {supported}"}), 400

    raw_key = request.form.get("api_key", "").strip()
    provider    = request.form.get("provider", "openai")

    # Built-in provider: use hardcoded config + server-side API key
    builtin = BUILTIN_PROVIDERS.get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model    = request.form.get("model", "").strip() or builtin["model"]
        api_key  = _get_builtin_key(provider)
        if not api_key:
            return jsonify({"error": f"\u670d\u52a1\u7aef\u672a\u914d\u7f6e {builtin['api_key_env']}\uff0c\u8bf7\u8054\u7cfb\u7ba1\u7406\u5458"}), 400
    else:
        use_server_key = TEST_MODE and (not raw_key or raw_key == SERVER_ENV_SENTINEL)
        base_url  = request.form.get("base_url", "").strip() or DEFAULT_BASE_URL
        api_key   = DEFAULT_API_KEY if use_server_key else (raw_key or DEFAULT_API_KEY)
        model     = request.form.get("model", "").strip() or DEFAULT_MODEL

    if not all([base_url, api_key, model]):
        return jsonify({"error": "\u8bf7\u586b\u5199 Base URL\u3001API Key \u548c Model\uff0c\u6216\u914d\u7f6e\u670d\u52a1\u7aef\u9ed8\u8ba4\u503c"}), 400

    max_minutes = int(request.form.get("max_minutes", DEFAULT_MAX_CHUNK_MINUTES))
    max_mb      = int(request.form.get("max_mb", DEFAULT_MAX_CHUNK_MB))
    enable_diarization = request.form.get("enable_diarization", "false").lower() == "true"

    # Save uploaded file
    task_id = uuid.uuid4().hex[:12]
    save_path = str(UPLOAD_DIR / f"{task_id}{ext}")
    file.save(save_path)

    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)

    uid = current_user.id
    if uid not in tasks:
        tasks[uid] = {}

    tasks[uid][task_id] = {
        "status": "queued",
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "total_chunks": 0,
        "current_chunk": 0,
        "completed_chunks": 0,
        "chunk_results": [],
        "transcript": "",
        "error": "",
        "speakers": [],
        "diarization_error": "",
        "enable_diarization": enable_diarization,
    }

    # ── Persist task to SQLite ──
    try:
        TaskService.create_task(
            task_id=task_id,
            user_id=uid,
            filename=file.filename,
            file_size_mb=round(file_size_mb, 2),
            enable_diarization=enable_diarization,
            provider=provider,
            model=model,
        )
    except Exception as db_err:
        print(f"⚠️ DB create failed: {db_err}")

    t = threading.Thread(
        target=run_transcription,
        args=(task_id, save_path, base_url, api_key, model,
              max_minutes, max_mb, provider, uid, enable_diarization),
        daemon=True,
    )
    t.start()

    return jsonify({"task_id": task_id, "file_size_mb": round(file_size_mb, 2)})


@app.route("/api/status/<task_id>")
@login_required
def status(task_id):
    # Live in-memory data first (for active tasks with progress)
    user_tasks = tasks.get(current_user.id, {})
    task = user_tasks.get(task_id)
    if task:
        return jsonify(task)
    # Fall back to DB for completed/historical tasks
    db_task = TaskService.get_task(task_id, current_user.id)
    if db_task:
        return jsonify(db_task)
    return jsonify({"error": "\u4efb\u52a1\u4e0d\u5b58\u5728"}), 404


@app.route("/api/test-connection", methods=["POST"])
@login_required
def test_connection():
    data = request.json or {}
    raw_key = data.get("api_key", "").strip()
    use_server_key = TEST_MODE and (not raw_key or raw_key == SERVER_ENV_SENTINEL)
    base_url = data.get("base_url", "").strip() or DEFAULT_BASE_URL
    api_key  = DEFAULT_API_KEY if use_server_key else (raw_key or DEFAULT_API_KEY)
    model    = data.get("model", "").strip() or DEFAULT_MODEL
    provider = data.get("provider", "openai")

    if not all([base_url, api_key, model]):
        return jsonify({"ok": False, "error": "\u8bf7\u586b\u5199\u6240\u6709\u914d\u7f6e\u9879"}), 400

    try:
        if provider == "zhipu" and ZhipuAI:
            client = ZhipuAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="glm-4-flash",
                messages=[{"role": "user", "content": "Hi, reply with OK"}],
                max_tokens=10,
            )
        else:
            client = OpenAI(base_url=base_url, api_key=api_key)
            test_model = model
            if provider == "modelscope" and ("sensevoice" in model.lower() or "paraformer" in model.lower()):
                test_model = "qwen/Qwen2.5-7B-Instruct"

            resp = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Hi, reply with OK"}],
                max_tokens=10,
            )
        return jsonify({"ok": True, "reply": resp.choices[0].message.content})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/builtin-providers")
@login_required
def builtin_providers():
    """Tell the frontend which built-in providers have server-side keys."""
    available = {}
    for name, info in BUILTIN_PROVIDERS.items():
        has_key = bool(_get_builtin_key(name))
        available[name] = {
            "available": has_key,
            "model": info["model"],
        }
    return jsonify(available)


@app.route("/api/test-config")
@login_required
def test_config():
    demo_files = []
    if DEMO_AUDIO_DIR.exists():
        for f in sorted(DEMO_AUDIO_DIR.iterdir()):
            if f.suffix.lower() in SUPPORTED_EXTENSIONS and not f.name.startswith("."):
                size_mb = f.stat().st_size / (1024 * 1024)
                demo_files.append({"name": f.name, "size_mb": round(size_mb, 2)})
    return jsonify({
        "test_mode": TEST_MODE,
        "has_config": bool(DEFAULT_BASE_URL and DEFAULT_API_KEY and DEFAULT_MODEL),
        "base_url": DEFAULT_BASE_URL if TEST_MODE else "",
        "model": DEFAULT_MODEL if TEST_MODE else "",
        "api_key_set": bool(DEFAULT_API_KEY) if TEST_MODE else False,
        "demo_files": demo_files,
    })


@app.route("/api/demo-file/<path:filename>")
@login_required
def serve_demo_file(filename):
    if not DEMO_AUDIO_DIR.exists():
        return jsonify({"error": "demo_audio directory not found"}), 404
    safe_name = Path(filename).name
    file_path = DEMO_AUDIO_DIR / safe_name
    if not file_path.exists() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(str(DEMO_AUDIO_DIR), safe_name)




# ================================================================

if __name__ == "__main__":
    print("Audio Transcriber running on http://localhost:5099")
    app.run(host="0.0.0.0", port=5099, debug=False)
