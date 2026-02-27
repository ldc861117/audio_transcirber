# [Phase1 Track B] 订阅 Plan & 配额 Quota 系统

## 目标

实现用户订阅计划和 API 用量配额系统，为商业化打基础。

## 必读文档

- `contracts.yaml` — 重点看 `plan_tier_enum`, `plan_definitions`, `user_plan`, `quota_usage`
- `auth.py` — 理解用户模型和认证方式
- `AGENTS.md` — 开发规范

## ⚠️ 严格文件边界

**只能创建/修改：**

- `plans/plan_config.py`
- `plans/plan_db.py`
- `services/plan_service.py`
- `services/quota_service.py`
- `routes/plan_routes.py`
- `tests/test_plan_service.py`

**绝不修改：**

- `app.py`, `auth.py`, `speaker.py`, `speaker_db.py`
- `static/*`, `contracts.yaml`

## 子任务

### 1. Plan 配置 — `plans/plan_config.py`

- 从 `contracts.yaml` 的 `plan_definitions` 加载 Plan 定义
- 提供 `get_plan_config(tier: str) -> dict` 函数
- Plan 等级：free / basic / pro

### 2. 数据库层 — `plans/plan_db.py`

- 创建 `user_plans` 表：user_id, tier, monthly_minutes, used_minutes, expires_at, created_at, updated_at
- 创建 `quota_usage` 表：id, user_id, task_id, minutes_used, created_at
- 数据库文件路径：`data/plans.db`
- 新用户默认分配 `free` Plan

### 3. 服务层 — `services/plan_service.py`

```python
class PlanService:
    def get_user_plan(user_id) -> dict        # 返回当前 Plan + 用量
    def subscribe(user_id, tier) -> bool       # 订阅/升级
    def get_available_plans() -> list[dict]    # 所有可用 Plan
```

### 4. 服务层 — `services/quota_service.py`

```python
class QuotaService:
    def check_quota(user_id, estimated_minutes) -> dict
        # 返回 {"allowed": bool, "remaining": float, "plan": str}
    def deduct_quota(user_id, task_id, minutes_used) -> bool
    def get_usage_summary(user_id) -> dict
        # 返回 {"total_used": float, "quota": int, "remaining": float, "history": [...]}
```

### 5. 路由层 — `routes/plan_routes.py`

- Blueprint: `plan_bp = Blueprint("plans", __name__, url_prefix="/api/v1/plans")`
- `GET /` — 可用 Plan 列表
- `GET /me` — 当前用户 Plan & 用量余额
- `POST /subscribe` — 订阅/升级 `{"tier": "basic"}`
- `GET /usage` — 用量历史
- 所有路由需 `@login_required`

### 6. 测试 — `tests/test_plan_service.py`

- 测试默认 Plan 分配
- 测试配额检查逻辑
- 测试配额扣减

## 验收标准

1. `python -m py_compile plans/plan_config.py plans/plan_db.py services/plan_service.py services/quota_service.py routes/plan_routes.py`
2. `python -c "from services.quota_service import QuotaService"`
3. `python -c "from routes.plan_routes import plan_bp"`

## 集成点

- 在 `app.py` 的 `upload()` 路由前调用 `QuotaService.check_quota()`
- 在 `run_transcription()` 完成后调用 `QuotaService.deduct_quota()`
- 这些集成步骤 **不在本 Track 范围内**

## 环境说明

- Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: `pip install -r requirements.txt`
- 如果依赖安装失败，跳过测试，直接提交代码
