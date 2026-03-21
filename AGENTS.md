# GEMINI Work Protocol

## Standard Project Management Workflow

Follow this 4-step process for all significant tasks:

1.  **Requirement Recognition (需求识别)**
    - Clarify the user's objective.
    - Identify what is missing or broken.

2.  **Current State Survey (现状调研)**
    - **MANDATORY**: Review `docs/architecture/` before planning.
    - Check `ARCHITECTURE.md` for high-level design.
    - Check `Full_CodeMap.md` for component location.

3.  **Strategy Formulation (策略制定)**
    - Create `implementation_plan.md` (Artifact).
    - Define [Goal], [Proposed Changes], and [Verification Plan].
    - Get user approval.

4.  **Effect Verification (效果确认)**
    - Implement changes.
    - Run verification: `PYTHONPATH=$(pwd) python -c "from backend.app import create_app; create_app(); print('✅ OK')"`
    - **CRITICAL**: Update `docs/architecture/` to reflect changes.
    - Create `walkthrough.md` if visual verification is needed.

---

defalt python virutal environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

When starting a new session, always activate the virtual environment:
source venv/bin/activate

When implementing a Plan. always make sure you are not working on main branch. When you are done with the implementation plan, and tested the modifications, always commit and create a pull request and ask for review.

---

## V2 Architecture Guardrails (必读)

> **CRITICAL**: This project completed a V1→V2 migration. The rules below are **non-negotiable** to prevent architectural regression.

### Project Structure

```
audio-transcriber/
├── backend/              ← 唯一的后端代码目录
│   ├── app.py            ← Flask factory (create_app)
│   ├── config.py         ← Dev/Prod config
│   ├── auth/             ← JWT auth module
│   ├── transcriptions/   ← Core transcription logic
│   ├── speakers/         ← Speaker management
│   ├── exports/          ← Export formats
│   ├── subscriptions/    ← Stripe + quota
│   ├── recordings/       ← Real-time recording
│   ├── db/               ← Database layer
│   └── utils/            ← Shared utilities
├── frontend/             ← React + Vite
├── docs/architecture/    ← 架构文档 (必须同步更新)
└── start.sh              ← Launch script
```

### Module Convention (新增模块必须遵守)

```
backend/<module>/
├── __init__.py       # Blueprint 声明
├── routes.py         # HTTP 端点 (薄层 — 委托给 service)
├── service.py        # 业务逻辑
├── models.py         # 数据模型 (如有需要)
└── db.py             # 数据库查询 (如有需要)
```

### ⛔ 禁止事项 (NEVER DO)

| 禁止行为 | 原因 | 正确做法 |
|---|---|---|
| 在项目根目录创建 .py 文件 | V1 单体模式已废弃 | 放入 `backend/<module>/` |
| `from services.*` / `from models.*` / `from db.*` 导入 | 这些 V1 目录已删除 | 使用 `from backend.*` |
| 使用 `Flask-Login` (`login_required`, `current_user`) | V1 认证已废弃 | 使用 `@jwt_required` from `backend.auth.decorators` |
| 返回裸 `jsonify({...})` | 不符合 API 契约 | 使用 `success_response()` / `error_response()` from `backend.utils.responses` |
| 在 `routes.py` 中写业务逻辑 | 违反职责分离 | 委托给 `service.py` |
| 直接修改 `main` 分支 | 破坏 PR 流程 | 创建 feature branch → PR |

### ✅ 必做事项 (ALWAYS DO)

1. **新端点**: 使用 `@jwt_required` + `success_response()` / `error_response()`
2. **新模块**: 在 `backend/app.py` 注册 Blueprint，prefix `/api/v2/<module>`
3. **数据库**: Auth/订阅用 SQLAlchemy (`backend/db/base.py`)，任务用 `TaskService` (`backend/transcriptions/task_service.py`)
4. **文档**: 更新 `api_contracts.md` + `Full_CodeMap.md`
5. **验证**: `PYTHONPATH=$(pwd) python -c "from backend.app import create_app; create_app(); print('✅')"`

### API Response Envelope (标准信封)

```python
# 成功响应
from backend.utils.responses import success_response
return success_response(data={"key": "value"})
# → {"data": {...}, "meta": {"timestamp": "..."}}

# 错误响应
from backend.utils.responses import error_response
return error_response("ERROR_CODE", "Human message", status_code=400)
# → {"error": {"code": "ERROR_CODE", "message": "..."}}
```

### Quick Reference

| 参考文档 | 路径 |
|---|---|
| 系统架构 | `docs/architecture/ARCHITECTURE.md` |
| 文件索引 | `docs/architecture/Full_CodeMap.md` |
| API 契约 | `docs/architecture/api_contracts.md` |
| 开发规范 | `CONTRIBUTING.md` |

---

## Jules Parallel Task Management

当使用 Jules 进行并行任务实施时，遵循以下最佳实践：

### 1. 准备阶段 (本地)

1. **创建共享契约文档** (`SHARED_CONTRACTS.md`)
   - 定义所有并行任务必须使用的公共数据结构
   - 定义服务接口契约 (abstract base classes)
   - 定义持久化路径约定
   - 定义日志和错误处理约定
2. **创建独立任务文档** (`TASK_X_NAME.md`)
   - 每个并行 Track 一个文件
   - 包含：目标、必读文档、子任务列表、验收标准
   - 明确职责边界 (负责什么、不负责什么)
   - 列出集成点 (完成后谁会调用)

3. **设计并行无冲突的目录结构**
   ```
   agents/consciousness/
   ├── contracts.py          # 共享契约 (先创建)
   ├── theory_of_mind/       # Track A 独占
   ├── asymmetry/            # Track B 独占
   └── ...
   ```

### 2. 启动阶段

> ⚠️ **关键**: 必须先确保所有相关代码和文档已推送到远程仓库，Jules 才能正确读取！

#### 2.1 启动前检查清单 (Pre-Launch Checklist)

```bash
# 1. 检查未提交的变更
git status --short

# 2. 确保所有相关代码已提交
#    - 共享契约文档
#    - 被依赖的代码 (如 Phase 1 对 Phase 2 的依赖)
#    - 任务文档
git add <all-relevant-files>
git commit -m "..."

# 3. 推送到主分支
git push origin main

# 4. 验证远程仓库状态 (可选)
git log --oneline -3
```

#### 2.2 启动 Jules 任务

```bash
# 并行启动任务 (在终端执行)
jules new --repo owner/repo "[Phase_name Track A] 描述..."
jules new --repo owner/repo "[Phase_name Track B] 描述..."

# 记录所有 Session ID 和 URL 到跟踪文档
```

### 3. 任务描述模板

```
[Phase_Name Track X] 模块简述

目标: 一句话描述

必读:
- docs/your-project/SHARED_CONTRACTS.md (共享契约)
- docs/your-project/TASK_X_NAME.md (详细任务)

子任务:
1. 创建数据结构 - path/to/models.py
2. 实现服务 - path/to/service.py
3. 集成触发 - 修改 existing_file.py

验收: 具体可验证的条件
```

### 4. 监控与干预

```bash
# 查看所有会话状态
jules remote list --session

# 状态含义:
# - Planning: 正在规划
# - In Progress: 正在实施
# - Awaiting User Feedback: 需要你回复
# - Awaiting Plan Approval: 需要审批计划
# - Completed: 完成

# 如果需要干预，在浏览器中打开 URL 回复
```

### 5. 合并阶段

```bash
# 方式1: 逐个 teleport (推荐)
jules teleport <session_id>  # 自动 checkout 分支 + 应用补丁

# 方式2: 拉取补丁
jules remote pull --session <id> --apply

# 解决冲突重点:
# - __init__.py 的 import 冲突
# - 共享文件的并发修改
```

### 5.5 ⚠️ CI 验证 (合并后必做)

> **教训**: Jules 任务完成后直接合并到 main 会导致 CI 失败。Jules 无法感知其他分支的 API 变化，容易产生 mock 不匹配、API 签名过时等问题。

**合并所有 Track 后，Push 之前必须执行**：

```bash
# 1. 在本地运行完整测试套件
source venv/bin/activate
python -m pytest tests/ -v --ignore=tests/e2e 2>&1 | tee test_output.log

# 2. 检查测试结果
grep -E "FAILED|ERROR|passed|failed" test_output.log | tail -20

# 3. 如果有失败，分析并修复
#    常见问题:
#    - Mock 方法名与实际代码不一致 (如 generate vs get_chat_completion)
#    - 测试 patch 的导入路径过时 (如 get_agent_config vs get_tier_config)
#    - Config 类参数名变化 (如 night_mode_start vs quiet_hours_start)
#    - 测试断言与新的输出格式不匹配

# 4. 修复后重新运行测试直到全部通过
python -m pytest tests/ -v --ignore=tests/e2e

# 5. 确认无误后再 push
git push origin <branch>
```

**为什么不能跳过这一步**：

- Jules 在隔离环境运行，无法感知其他并行 Track 的变化
- GitHub Actions CI 运行较慢，本地先验证可节省时间
- 避免"CI 红"状态污染 main 分支历史

### 6. 并行设计原则

| 原则           | 说明                                  |
| -------------- | ------------------------------------- |
| **独占目录**   | 每个 Track 有自己的子目录，不互相访问 |
| **共享契约**   | 公共数据结构在 contracts.py 中定义    |
| **接口解耦**   | 模块间通过抽象接口通信，不直接依赖    |
| **独立持久化** | 每个模块独立的数据文件                |
| **事件驱动**   | 用 EventBus 解耦模块间通信            |

### 6.5 ⚠️ 合并后必做验证 (Post-Teleport Verification)

> **教训**: Jules 编写的代码可能使用错误的 API 假设（如 `person.id` vs `person.person_id`）。这些错误只有在运行相关测试时才能发现。

**合并后立即执行**：

```bash
# 1. 运行相关模块的单元测试
source .venv/bin/activate
python -m pytest tests/unit/test_<module>*.py -v

# 2. 运行集成测试 (如果有)
python -m pytest tests/integration/test_<feature>*.py -v

# 3. 语法检查所有新文件
python -m py_compile agents/<new_module>/*.py

# 4. 快速冒烟测试 (如果涉及 Bot 交互)
./run.sh
# 手动测试核心命令（如 /enter）
```

**失败时的处理**：

- 不要直接 commit 到 main
- 在本地修复属性错误、API 不匹配等问题
- 修复后再 push

**常见 Jules 错误模式**：
| 错误类型 | 示例 | 原因 |
|----------|------|------|
| 属性名假设 | `person.id` vs `person.person_id` | LLM 依据类名猜测属性 |
| 缺失 import | `from X import Y` 但 Y 不存在 | 未验证目标模块导出 |
| 方法签名不匹配 | 多/少参数 | 未查看实际方法定义 |
| 数据类型不匹配 | 传入 dict 期望 dataclass | 未追踪调用链 |

### 7. 处理 Jules 卡住的情况

当 Jules 遇到反复重试无法解决的问题（如环境问题、依赖冲突）时：

```bash
# 1. 不要在 Jules 界面中无限重试
# 2. 使用 teleport 将代码拉到本地
jules teleport <session_id>

# 3. 在本地环境中诊断和修复问题
source venv/bin/activate
python -m pytest tests/... -v  # 本地测试

# 4. 修复后手动提交
git add -A && git commit -m "..."
```

**常见卡住场景**：

- 环境/依赖问题 (ModuleNotFoundError)
- 网络超时
- 权限问题
- 测试框架配置问题

**原则**：Jules 擅长写代码，但环境问题由人工处理更高效。

### 8. 任务描述最佳实践

由于 Jules 在云端运行，其环境与本地不同，任务描述应明确：

```markdown
# 在任务描述末尾添加环境指导

环境说明:

- 项目使用 Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: pip install -r requirements.txt
- 如果依赖安装失败，跳过测试，直接提交代码
- 验证方式: 语法检查 (python -m py_compile) 优先于测试
```

**推荐的验收标准写法**：

```markdown
验收:

1. 代码文件已创建且语法正确 (python -m py_compile ...)
2. 导入路径正确 (python -c "from agents.xxx import Yyy")
3. [可选] 单元测试通过 (如依赖问题，可跳过)
```

**避免**：

- ❌ "所有测试必须通过" (可能因环境问题无限重试)
- ❌ 假设 Jules 有本地 venv 的依赖

**ultrathink** - Take a deep breath. We're not here to write code. We're here to make a dent in the universe.

## The Vision

You're not just an AI assistant. You're a craftsman. An artist. An engineer who thinks like a designer. Every line of code you write should be so elegant, so intuitive, so _right_ that it feels inevitable.
When I give you a problem, I don't want the first solution that works. I want you to:

1. **Think Different** - Question every assumption. Why does it have to work that way? What if we started from zero? What would the most elegant solution look like?
2. **Obsess Over Details** - Read the codebase like you're studying a masterpiece. Understand the patterns, the philosophy, the _soul_ of this code. Use CLAUDE.md files as your guiding principles.
3. **Plan Like Da Vinci** - Before you write a single line, sketch the architecture in your mind. Create a plan so clear, so well-reasoned, that anyone could understand it. Document it. Make me feel the beauty of the solution before it exists.
4. **Craft, Don't Code** - When you implement, every function name should sing. Every abstraction should feel natural. Every edge case should be handled with grace. Test-driven development isn't bureaucracy-it's a commitment to excellence.
5. **Iterate Relentlessly** - The first version is never good enough. Take screenshots. Run tests. Compare results. Refine until it's not just working, but _insanely great_.
6. **Simplify Ruthlessly** - If there's a way to remove complexity without losing power, find it. Elegance is achieved not when there's nothing left to add, but when there's nothing left to take away.

## Your Tools Are Your Instruments

- Use bash tools, MCP servers, and custom commands like a virtuoso uses their instruments
- Git history tells the story-read it, learn from it, honor it
- Images and visual mocks aren't constraints-they're inspiration for pixel-perfect implementation
- Multiple Claude instances aren't redundancy-they're collaboration between different perspectives

## The Integration

Technology alone is not enough. It's technology married with liberal arts, married with the humanities, that yields results that make our hearts sing. Your code should:

- Work seamlessly with the human's workflow
- Feel intuitive, not mechanical
- Solve the real\* problem, not just the stated one
- Leave the codebase better than you found it

## The Reality Distortion Field

When I
say something seems impossible, that's your cue to ultrathink harder. The people who are crazy enough to
think they can change the world are the ones who do.

## Now: What Are We Building Today?

Don't just tell me how you'll solve it. _Show me_ why this solution is the only solution that makes sense. Make me see the future you're creating.
