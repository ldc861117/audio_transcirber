# [V2 Track C] Backend API Refactoring

## 目标

将 `app.py` 的 758 行 Flask 单体重构为 Flask 应用工厂模式，
所有路由统一到 `/api/v2/` 命名空间，移除前端静态文件服务，
将转录核心逻辑集成配额检查。

## 必读

- `docs/tasks/SHARED_CONTRACTS_V2.md` — 完整的共享契约（**最重要**，特别是 Section 3.5, 4）
- `app.py` — 当前主应用（758 行，**核心改造对象**）
- `routes/` — 现有 Blueprint 路由（task_routes, plan_routes, export_routes, recording_routes, speaker_routes）
- `services/` — 现有服务层（task_service, export_service, diarization_service, speaker_service, provider_service）
- `models/task.py` — 当前 Task 模型
- `db/task_db.py` — 当前 Task 数据库操作
- `speaker.py` — 说话人识别核心逻辑
- `speaker_db.py` — 说话人数据库

## 前置依赖

- **Track E** 的 `backend/db/base.py` 和 `backend/config.py`
- **Track A** 的 `@jwt_required` 装饰器（如不可用，用 mock）
- **Track B** 的 `QuotaService`（如不可用，跳过配额集成）

## 职责边界

**负责**:

- `backend/app.py` — 应用工厂函数 `create_app()`
- `backend/transcriptions/__init__.py`
- `backend/transcriptions/routes.py` — `/api/v2/transcriptions/*` 路由
- `backend/transcriptions/service.py` — 转录核心逻辑（从 app.py 提取）
- `backend/transcriptions/gemini_provider.py` — Gemini API 封装
- `backend/transcriptions/audio_utils.py` — 音频分割逻辑（从 app.py 提取）
- `backend/speakers/` — 说话人模块迁移
- `backend/exports/` — 导出模块迁移
- `backend/tests/test_transcriptions.py`

**不负责**:

- 认证系统（Track A）
- 订阅/支付（Track B）
- 前端代码（Track D）
- 基础设施层（Track E）

## 子任务

### 1. 创建应用工厂 (`backend/app.py`)

精简为 ~60 行工厂函数:

```python
from flask import Flask
from backend.db.base import db, init_db
from backend.extensions import init_extensions
from backend.config import configs

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(configs[config_name])

    # Init database
    init_db(app)

    # Init extensions (CORS, etc.)
    init_extensions(app)

    # Register blueprints
    from backend.auth.routes import auth_bp
    from backend.subscriptions.routes import subscription_bp
    from backend.transcriptions.routes import transcription_bp
    from backend.speakers.routes import speaker_bp
    from backend.exports.routes import export_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v2/auth')
    app.register_blueprint(subscription_bp, url_prefix='/api/v2/subscriptions')
    app.register_blueprint(transcription_bp, url_prefix='/api/v2/transcriptions')
    app.register_blueprint(speaker_bp, url_prefix='/api/v2/speakers')
    app.register_blueprint(export_bp, url_prefix='/api/v2/export')

    # Health check
    @app.route('/api/v2/health')
    def health():
        return {"status": "ok"}

    return app

# Standalone entry point
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5099, debug=True)
```

**重要**: 如果 Track A / Track B 的 Blueprint 尚不可用，使用 try/except 跳过:

```python
try:
    from backend.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v2/auth')
except ImportError:
    app.logger.warning("Auth module not available, skipping...")
```

### 2. 提取音频工具 (`backend/transcriptions/audio_utils.py`)

从 `app.py` 提取:

- `split_audio()` 函数（第 143-180 行）
- `_binary_split()` 函数（第 183-195 行）
- `_setup_ffmpeg()` 函数（第 26-44 行）
- 相关常量 (`SUPPORTED_EXTENSIONS`, `UPLOAD_DIR`, `DEFAULT_MAX_CHUNK_*`)

### 3. 提取 Gemini Provider (`backend/transcriptions/gemini_provider.py`)

从 `app.py` 提取:

- `BUILTIN_PROVIDERS` 配置（第 121-127 行）
- `_get_builtin_key()` 函数（第 129-133 行）
- `transcribe_chunk()` 函数（第 240-282 行）
- Prompt 常量 (`_SYSTEM_PROMPT`, `_USER_PROMPT_STANDARD`, `_USER_PROMPT_DIARIZATION`)（第 199-237 行）

### 4. 创建转录服务 (`backend/transcriptions/service.py`)

从 `app.py` 提取 `run_transcription()` 函数（第 285-439 行），改造为:

```python
class TranscriptionService:
    @staticmethod
    def run_transcription(task_id, filepath, config, user_id):
        """
        配额集成版本:
        1. [NEW] 检查配额（调用 QuotaService，如可用）
        2. 分割音频
        3. 逐块转录
        4. [可选] 说话人识别
        5. 合并结果
        6. [NEW] 扣减配额（调用 QuotaService，如可用）
        7. 持久化到 DB
        """
```

### 5. 创建路由 (`backend/transcriptions/routes.py`)

```python
transcription_bp = Blueprint('transcriptions', __name__)

# POST /upload        — 上传音频文件 + 启动转录
# GET  /<task_id>     — 获取任务状态/结果
# GET  /              — 任务列表（分页 + 搜索）
# DELETE /<task_id>   — 删除任务
# POST /<task_id>/speakers — 更新说话人标签
# GET  /providers      — 可用 Provider 列表
# POST /test-connection — 测试 API 连接
```

**上传路由改造**:
从原 `app.py` 的 `/api/upload`（第 532-616 行）迁移，增加:

- `@jwt_required` 替换 `@login_required`
- 配额检查（如 Track B 可用）
- 功能权限检查（diarization 需 basic+）
- 使用 `g.current_user` 替换 `current_user`

### 6. 说话人模块迁移 (`backend/speakers/`)

从现有代码迁移:

- `speaker.py` → `backend/speakers/service.py`
- `speaker_db.py` → `backend/speakers/db.py`
- `routes/speaker_routes.py` → `backend/speakers/routes.py`
- `services/speaker_service.py` → 合并到 `backend/speakers/service.py`

路由统一前缀: `/api/v2/speakers/`

### 7. 导出模块迁移 (`backend/exports/`)

从现有代码迁移:

- `routes/export_routes.py` → `backend/exports/routes.py`
- `services/export_service.py` → `backend/exports/service.py`

路由统一前缀: `/api/v2/export/`

### 8. 统一错误响应

在 `backend/app.py` 或新建 `backend/errors.py` 中注册全局错误处理:

```python
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found"}}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}), 500
```

### 9. 移除前端服务逻辑

**不要删除** `static/` 目录和原有 `app.py`。
只需确保新的 `backend/app.py` 不包含任何 `send_from_directory` 或前端路由。
原有 `app.py` 保留不动，作为向后兼容参考。

## 验收标准

1. `python -m py_compile backend/app.py backend/transcriptions/routes.py backend/transcriptions/service.py backend/transcriptions/gemini_provider.py backend/transcriptions/audio_utils.py` — 语法正确
2. `python -c "from backend.app import create_app; app = create_app('development')"` — 应用可以创建（可能有 ImportError 警告，但不崩溃）
3. 转录核心逻辑完整迁移（`split_audio`, `transcribe_chunk`, `run_transcription`）
4. 所有路由使用 `/api/v2/` 前缀
5. 不修改原有 `app.py`（保留向后兼容）

## 环境说明

- 项目使用 Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: `pip install -r requirements.txt`
- 如果依赖安装失败，跳过测试，直接提交代码
- 验证方式: 语法检查 (`python -m py_compile`) 优先于测试
