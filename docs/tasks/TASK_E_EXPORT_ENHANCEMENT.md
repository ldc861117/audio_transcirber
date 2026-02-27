# [Phase1 Track E] 多格式导出 (SRT/Word/PDF)

## 目标

在现有 TXT/Markdown 下载基础上，新增 SRT 字幕、Word 文档、PDF 三种专业导出格式。

## 必读文档

- `contracts.yaml` — 重点看 `export_format_enum` 和 `transcription_record`
- `app.py` — 理解当前的转写结果数据格式（`task["transcript"]`, `task["speakers"]`）
- `AGENTS.md` — 开发规范

## ⚠️ 严格文件边界

**只能创建/修改：**

- `services/export_service.py`
- `routes/export_routes.py`
- `templates/` — Word 模板等
- `tests/test_export_service.py`

**绝不修改：**

- `app.py`, `auth.py`, `speaker.py`, `speaker_db.py`
- `static/*`, `contracts.yaml`

## 子任务

### 1. 导出服务 — `services/export_service.py`

```python
class ExportService:
    def export_srt(self, transcript: str, speakers: list = None) -> str:
        """
        将转写结果转换为 SRT 字幕格式。

        如果有 speakers 数据（含时间戳），直接用时间戳。
        如果没有时间戳，按段落自动分配序号（无精确时间）。

        输出格式:
        1
        00:00:00,000 --> 00:00:15,300
        【说话人1】转写内容...

        2
        00:00:15,300 --> 00:00:28,700
        【说话人2】转写内容...
        """

    def export_word(self, transcript: str, metadata: dict = None,
                    speakers: list = None) -> bytes:
        """
        导出为 Word 文档 (.docx)。

        包含:
        - 标题页：文件名、日期、时长
        - 正文：带说话人标注的格式化转写
        - 说话人用不同颜色或加粗区分

        Returns: .docx 文件的字节内容
        """

    def export_pdf(self, transcript: str, metadata: dict = None,
                   speakers: list = None) -> bytes:
        """
        导出为 PDF。
        使用 reportlab 生成，支持中文。

        Returns: .pdf 文件的字节内容
        """
```

### 2. 路由层 — `routes/export_routes.py`

- Blueprint: `export_bp = Blueprint("export", __name__, url_prefix="/api/v1/export")`
- `POST /<task_id>` — 导出指定任务的转写结果
  - Request body: `{"format": "srt" | "docx" | "pdf"}`
  - Response: 文件下载 (Content-Disposition: attachment)
  - 需要 `@login_required`，scope 到 `current_user.id`

**注意**：由于 Track A（持久化）可能还未集成，这个路由需要同时支持：

1. 从内存 `tasks` 字典读取（当前模式）
2. 将来从数据库读取（集成后）

建议：路由接收 `transcript` 和 `speakers` 作为 POST body，而非从后端查询：

```python
@export_bp.route("/<task_id>", methods=["POST"])
@login_required
def export_task(task_id):
    data = request.json or {}
    fmt = data.get("format", "txt")
    transcript = data.get("transcript", "")
    speakers = data.get("speakers", [])
    metadata = data.get("metadata", {})
    # ...生成并返回文件
```

### 3. SRT 格式详细规范

```
序号
HH:MM:SS,mmm --> HH:MM:SS,mmm
字幕文本（可多行）

序号
...
```

时间戳格式要求：

- 小时、分钟、秒用冒号分隔
- 毫秒用逗号分隔（不是点号）
- 如果没有精确时间戳，按 5 秒间隔估算

### 4. 依赖管理

需要新增的 Python 依赖（只在 requirements.txt 末尾追加）：

```
python-docx>=0.8.11
reportlab>=4.0
```

### 5. 测试 — `tests/test_export_service.py`

- 测试 SRT 格式输出的正确性
- 测试 Word 文档字节输出（验证不为空且是有效 zip）
- 测试 PDF 字节输出（验证不为空且以 %PDF 开头）
- 测试无说话人数据时的退化处理

## 验收标准

1. `python -m py_compile services/export_service.py routes/export_routes.py`
2. `python -c "from services.export_service import ExportService; es = ExportService(); print(es.export_srt('测试内容'))"`
3. `python -c "from routes.export_routes import export_bp"`

## 集成点

- `app.register_blueprint(export_bp)` 注册到 Flask app
- 前端增加导出按钮（Track F 负责或后续实现）
- 这些集成步骤 **不在本 Track 范围内**

## 环境说明

- Python 3.11+
- 需安装: `pip install python-docx reportlab`
- 如果依赖安装失败，跳过测试，直接提交代码
