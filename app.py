"""
Audio Transcription App — 音频自动切分与转写
Flask backend: receives audio files, splits them with pydub,
transcribes each chunk via an OpenAI-compatible Gemini API, and
merges results.
"""

import os
import uuid
import base64
import tempfile
import threading
import traceback
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pydub import AudioSegment
from openai import OpenAI
try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

load_dotenv()

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

UPLOAD_DIR = Path(tempfile.gettempdir()) / "audio_transcriber_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# All audio formats supported by ffmpeg / pydub
SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a",
    ".wma", ".aiff", ".aif", ".opus", ".amr", ".ape",
    ".ac3", ".webm", ".caf", ".spx", ".oga", ".wv",
    ".mp4", ".mov", ".mkv",  # video files with audio track
}

# In-memory task store  {task_id: {...}}
tasks: dict[str, dict] = {}

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
        "model": "gemini-2.5-flash",
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
    """Recursively halve a segment until each piece is ≤ max_mb."""
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


def transcribe_chunk(chunk_path: str, client, model: str, provider: str = "openai") -> str:
    """Send a single audio chunk to the appropriate API and return text."""
    if provider == "zhipu" and ZhipuAI and isinstance(client, ZhipuAI) and ("asr" in model.lower() or model == "glm-asr-2512"):
        # Use Zhipu SDK for dedicated ASR
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model,
                file=f,
            )
        return response.text

    if provider == "modelscope":
        # ModelScope Serverless API is OpenAI-compatible for ASR
        with open(chunk_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model=model,
                file=f,
                response_format="text"
            )
        return response if isinstance(response, str) else response.text

    # Default: OpenAI-compatible Multimodal Chat completion
    mime = "audio/mpeg" if chunk_path.endswith(".mp3") else "audio/mp4"
    with open(chunk_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    kwargs = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一位拥有 20 年经验的专业会议速记员和纪要专家。"
                    "你的任务是将音频内容转化为“智能逐字稿”（Intelligent Verbatim）。"
                    "核心原则：保持内容的完整性和准确性，同时提升阅读体验。"
                    "重要：请始终使用简体中文（Simplified Chinese）输出，不要使用繁体中文。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "请对以下音频进行专业转写。遵循以下业界标准规范：\n\n"
                            "1. **智能净化**：\n"
                            "   - 剔除口语废话（如“那个”、“呃”、“嗯”、“就是说”等），除非表达迟疑或强调；\n"
                            "   - 修正明显的口误和重复（如“我...我们认为” -> “我们认为”）；\n"
                            "   - 保持原本的语序和逻辑，不要随意改写内容。\n\n"
                            "2. **格式规范**：\n"
                            "   - **说话人标记**：根据声纹和上下文区分说话人，使用【说话人1】、【说话人2】或具体称谓（如【主持人】、【经理】）标记；\n"
                            "   - **段落分明**：不同说话人必须换行。长段独白请根据逻辑语义合理分段；\n"
                            "   - **标点专业**：使用规范的中文全角标点。语气强烈的用感叹号，疑问用问号，并列用顿号。\n\n"
                            "3. **关键内容突出**：\n"
                            "   - 对于**关键数据**（金额、时间、数量）、**专有名词**（项目名、部门名、技术术语），请确保准确无误；\n"
                            "   - 如遇决策性结论或待办事项，保持原话，不要遗漏。\n\n"
                            "4. **混合语言处理**：\n"
                            "   - 中英文混杂时，英文单词前后保留空格（如“使用 AI 技术”）。\n"
                            "   - 仅输出转写正文，不要包含“好的”、“以下是转写”等无关回复。"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                        },
                    },
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
                      max_minutes: int, max_mb: int, provider: str = "openai"):
    """Background worker: split → transcribe → merge."""
    task = tasks[task_id]
    try:
        # ── 1. Split ────────────────────────────────────────────
        task["status"] = "splitting"
        # Optimize format for Zhipu SDK (m4a is supported and efficient)
        pref_fmt = "m4a" if provider == "zhipu" else "mp3"
        chunks = split_audio(filepath, max_minutes, max_mb, preferred_format=pref_fmt)
        task["total_chunks"] = len(chunks)
        task["status"] = "transcribing"

        # ── 2. Transcribe each chunk ────────────────────────────
        if provider == "zhipu" and ZhipuAI:
            client = ZhipuAI(api_key=api_key)
        else:
            client = OpenAI(base_url=base_url, api_key=api_key)
        results: list[str] = []
        for i, chunk_path in enumerate(chunks):
            task["current_chunk"] = i + 1          # which chunk is being processed NOW
            task["completed_chunks"] = i            # how many are fully done
            try:
                text = transcribe_chunk(chunk_path, client, model, provider=provider)
                results.append(text)
                task["chunk_results"].append({
                    "index": i + 1,
                    "status": "done",
                    "text": text,
                })
            except Exception as e:
                err_msg = str(e)
                results.append(f"[片段 {i+1} 转写失败: {err_msg}]")
                task["chunk_results"].append({
                    "index": i + 1,
                    "status": "error",
                    "text": err_msg,
                })
            finally:
                task["completed_chunks"] = i + 1
                # Clean up chunk file
                try:
                    os.unlink(chunk_path)
                except OSError:
                    pass

        # ── 3. Merge ────────────────────────────────────────────
        task["transcript"] = "\n\n".join(results)
        task["status"] = "done"

    except Exception:
        task["status"] = "error"
        task["error"] = traceback.format_exc()
    finally:
        # Clean up uploaded file
        try:
            os.unlink(filepath)
        except OSError:
            pass


# ================================================================
#  Routes
# ================================================================

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "未收到音频文件"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return jsonify({"error": f"不支持的格式 {ext}，支持: {supported}"}), 400

    raw_key = request.form.get("api_key", "").strip()
    provider    = request.form.get("provider", "openai")

    # Built-in provider: use hardcoded config + server-side API key
    builtin = BUILTIN_PROVIDERS.get(provider)
    if builtin:
        base_url = builtin["base_url"]
        model    = request.form.get("model", "").strip() or builtin["model"]
        api_key  = _get_builtin_key(provider)
        if not api_key:
            return jsonify({"error": f"服务端未配置 {builtin['api_key_env']}，请联系管理员"}), 400
    else:
        use_server_key = TEST_MODE and (not raw_key or raw_key == SERVER_ENV_SENTINEL)
        base_url  = request.form.get("base_url", "").strip() or DEFAULT_BASE_URL
        api_key   = DEFAULT_API_KEY if use_server_key else (raw_key or DEFAULT_API_KEY)
        model     = request.form.get("model", "").strip() or DEFAULT_MODEL

    if not all([base_url, api_key, model]):
        return jsonify({"error": "请填写 Base URL、API Key 和 Model，或配置服务端默认值"}), 400

    max_minutes = int(request.form.get("max_minutes", DEFAULT_MAX_CHUNK_MINUTES))
    max_mb      = int(request.form.get("max_mb", DEFAULT_MAX_CHUNK_MB))

    # Save uploaded file
    task_id = uuid.uuid4().hex[:12]
    save_path = str(UPLOAD_DIR / f"{task_id}{ext}")
    file.save(save_path)

    file_size_mb = os.path.getsize(save_path) / (1024 * 1024)

    tasks[task_id] = {
        "status": "queued",
        "filename": file.filename,
        "file_size_mb": round(file_size_mb, 2),
        "total_chunks": 0,
        "current_chunk": 0,
        "completed_chunks": 0,
        "chunk_results": [],
        "transcript": "",
        "error": "",
    }

    t = threading.Thread(
        target=run_transcription,
        args=(task_id, save_path, base_url, api_key, model, max_minutes, max_mb, provider),
        daemon=True,
    )
    t.start()

    return jsonify({"task_id": task_id, "file_size_mb": round(file_size_mb, 2)})


@app.route("/api/status/<task_id>")
def status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task)


@app.route("/api/test-connection", methods=["POST"])
def test_connection():
    data = request.json or {}
    raw_key = data.get("api_key", "").strip()
    use_server_key = TEST_MODE and (not raw_key or raw_key == SERVER_ENV_SENTINEL)
    base_url = data.get("base_url", "").strip() or DEFAULT_BASE_URL
    api_key  = DEFAULT_API_KEY if use_server_key else (raw_key or DEFAULT_API_KEY)
    model    = data.get("model", "").strip() or DEFAULT_MODEL
    provider = data.get("provider", "openai")

    if not all([base_url, api_key, model]):
        return jsonify({"ok": False, "error": "请填写所有配置项"}), 400

    try:
        if provider == "zhipu" and ZhipuAI:
            client = ZhipuAI(api_key=api_key)
            # Test with a simple chat message
            resp = client.chat.completions.create(
                model="glm-4-flash",
                messages=[{"role": "user", "content": "Hi, reply with OK"}],
                max_tokens=10,
            )
        else:
            client = OpenAI(base_url=base_url, api_key=api_key)
            # For ModelScope or others, if the model is an ASR model, use a common LLM for connectivity test
            test_model = model
            if provider == "modelscope" and ("sensevoice" in model.lower() or "paraformer" in model.lower()):
                test_model = "qwen/Qwen2.5-7B-Instruct" # A reliable model on ModelScope for testing
            
            resp = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Hi, reply with OK"}],
                max_tokens=10,
            )
        return jsonify({"ok": True, "reply": resp.choices[0].message.content})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


@app.route("/api/builtin-providers")
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
    print("🎙️  Audio Transcriber running on http://localhost:5099")
    app.run(host="0.0.0.0", port=5099, debug=False)
