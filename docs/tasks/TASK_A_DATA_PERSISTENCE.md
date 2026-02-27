# [Phase1 Track A] 数据持久化 & 历史记录

## 目标

将转写任务从内存字典 (`tasks: dict`) 迁移到 SQLite 持久化存储，支持历史记录 CRUD。

## 必读文档

- `contracts.yaml` — 共享数据结构，重点看 `transcription_record` 和 `task_status_enum`
- `app.py` — 理解现有 `tasks` 字典结构 (line 52-54) 和 `run_transcription()` 流程
- `auth.py` — 理解 user_id 关联方式和 `@login_required` 装饰器
- `AGENTS.md` — 开发规范

## ⚠️ 严格文件边界

**只能创建/修改：**

- `db/task_db.py`
- `models/task.py`
- `services/task_service.py`
- `routes/task_routes.py`
- `tests/test_task_service.py`

**绝不修改：**

- `app.py`, `auth.py`, `speaker.py`, `speaker_db.py`
- `static/*`, `contracts.yaml`

## 子任务

### 1. 数据库层 — `db/task_db.py`

- 创建 `transcriptions` 表，字段映射 `contracts.yaml` 中的 `transcription_record`
- 提供 `_get_db()` 上下文管理器（参考 `auth.py` 的模式）
- 提供 `init_task_db()` 函数
- 数据库文件路径：`data/tasks.db`

### 2. 模型层 — `models/task.py`

- `TranscriptionRecord` dataclass，与 contracts 对齐
- 序列化/反序列化辅助方法

### 3. 服务层 — `services/task_service.py`

```python
class TaskService:
    def create_task(user_id, filename, file_size_mb, ...) -> str  # returns task_id
    def update_task(task_id, **kwargs) -> bool
    def get_task(task_id, user_id) -> dict | None
    def list_tasks(user_id, page=1, per_page=20, search="") -> dict  # {items, total, page}
    def delete_task(task_id, user_id) -> bool
```

### 4. 路由层 — `routes/task_routes.py`

- Flask Blueprint: `task_bp = Blueprint("tasks", __name__, url_prefix="/api/v1/transcriptions")`
- `GET /` — 列表（分页 `?page=1&per_page=20`，搜索 `?q=keyword`）
- `GET /<task_id>` — 详情
- `DELETE /<task_id>` — 删除
- 所有路由需 `@login_required`，且 scope 到 `current_user.id`

### 5. 测试 — `tests/test_task_service.py`

- 测试 CRUD 操作
- 测试用户隔离（user A 看不到 user B 的任务）

## 验收标准

1. `python -m py_compile db/task_db.py models/task.py services/task_service.py routes/task_routes.py`
2. `python -c "from services.task_service import TaskService"`
3. `python -c "from routes.task_routes import task_bp"`
4. [可选] `python -m pytest tests/test_task_service.py -v`

## 集成点

完成后，将在 `app.py` 中 `app.register_blueprint(task_bp)` 注册。
此步骤 **不在本 Track 范围内**。

## 环境说明

- Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: `pip install -r requirements.txt`
- 如果依赖安装失败，跳过测试，直接提交代码
- 验证方式: 语法检查 (py_compile) 优先于测试
