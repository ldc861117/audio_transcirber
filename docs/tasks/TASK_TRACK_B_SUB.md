# [V2 Track B] Subscription & Payment System

## 目标

实现 Stripe 集成的订阅管理系统：Plan 定义、Checkout 支付、Webhook 处理、
配额检查与扣减。支持 Mock 模式（无需真实 Stripe Key 也能运行）。

## 必读

- `docs/tasks/SHARED_CONTRACTS_V2.md` — 完整的共享契约（**最重要**，特别是 Section 3.3-3.6, 6）
- `plans/plan_config.py` — 当前 Plan 配置实现
- `plans/plan_db.py` — 当前 Plan 数据库操作
- `services/plan_service.py` — 当前 Plan 服务
- `services/quota_service.py` — 当前配额服务
- `contracts.yaml` — 当前 Plan 定义（YAML 格式）

## 前置依赖

- **Track E** 的 `backend/db/base.py` 和 `backend/config.py`
- 如果 Track E 尚未完成，请自行创建这些文件（按照 SHARED_CONTRACTS_V2.md 模板）

## 职责边界

**负责**:

- `backend/subscriptions/__init__.py`
- `backend/subscriptions/models.py` — Subscription + QuotaUsage + Invoice 模型
- `backend/subscriptions/plan_config.py` — Plan 定义（Python dict，替代 contracts.yaml）
- `backend/subscriptions/stripe_service.py` — Stripe API 集成
- `backend/subscriptions/quota_service.py` — 配额检查与扣减
- `backend/subscriptions/routes.py` — `/api/v2/subscriptions/*` 路由
- `backend/tests/test_subscriptions.py` — 单元测试

**不负责**:

- User 模型和认证逻辑（Track A）
- 转录流程（Track C）
- 前端定价页（Track D）

## 子任务

### 1. 创建模型 (`backend/subscriptions/models.py`)

按照 `SHARED_CONTRACTS_V2.md` Section 3.3, 3.4, 3.6 创建:

- `Subscription` 模型（含 stripe_customer_id, stripe_subscription_id 等）
- `QuotaUsage` 模型（记录每次用量）
- `Invoice` 模型（记录支付发票）

### 2. Plan 配置 (`backend/subscriptions/plan_config.py`)

按照 `SHARED_CONTRACTS_V2.md` Section 6 的定义，从 YAML 格式迁移为 Python dict:

```python
# Plan 定义常量
PLAN_DEFINITIONS = { ... }  # 来自 SHARED_CONTRACTS_V2.md Section 6

# 工具函数
def get_plan_config(tier: str) -> dict | None
def get_all_plans() -> dict
def get_plan_order() -> list  # ['free', 'basic', 'pro']
def is_tier_gte(tier_a: str, tier_b: str) -> bool  # tier_a >= tier_b?
```

### 3. Stripe 服务 (`backend/subscriptions/stripe_service.py`)

**Mock 模式**: 如果 `STRIPE_SECRET_KEY` 为空或以 `mock` 开头，所有 Stripe 调用使用 mock 数据。

```python
class StripeService:
    @staticmethod
    def create_customer(user) -> str:
        """创建 Stripe Customer，返回 customer_id"""

    @staticmethod
    def create_checkout_session(user_id: int, tier: str, cycle: str,
                                 success_url: str, cancel_url: str) -> str:
        """创建 Checkout Session，返回 session URL"""

    @staticmethod
    def create_portal_session(customer_id: str, return_url: str) -> str:
        """创建 Billing Portal Session，返回 URL"""

    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str) -> dict:
        """验证并处理 Webhook 事件"""

    @staticmethod
    def cancel_subscription(subscription_id: str) -> bool:
        """取消订阅（周期结束）"""

    @staticmethod
    def reactivate_subscription(subscription_id: str) -> bool:
        """重新激活已取消的订阅"""
```

**Webhook 事件处理**:

- `checkout.session.completed` → 更新 Subscription tier, stripe_subscription_id
- `invoice.paid` → 记录 Invoice, 重置月度配额
- `customer.subscription.updated` → 更新 tier, period, status
- `customer.subscription.deleted` → 降级为 free
- `invoice.payment_failed` → 标记 status = 'past_due'

### 4. 配额服务 (`backend/subscriptions/quota_service.py`)

迁移自 `services/quota_service.py`，增加功能:

```python
class QuotaService:
    @staticmethod
    def check_quota(user_id: int, estimated_minutes: float = 0,
                    file_size_mb: float = 0) -> dict:
        """
        完整的配额检查:
        - 月度分钟数
        - 单文件时长限制
        - 单文件大小限制
        返回 {"allowed": bool, "remaining": float, "plan": str, "error": str|None}
        """

    @staticmethod
    def check_feature(user_id: int, feature: str) -> bool:
        """检查功能是否可用（如 diarization, api_access）"""

    @staticmethod
    def deduct_quota(user_id: int, task_id: str, minutes_used: float) -> bool:
        """扣减配额"""

    @staticmethod
    def get_usage_summary(user_id: int) -> dict:
        """返回用量摘要"""

    @staticmethod
    def reset_monthly_quota(user_id: int) -> bool:
        """重置月度配额（Webhook 触发）"""
```

### 5. 路由 (`backend/subscriptions/routes.py`)

```python
subscription_bp = Blueprint('subscriptions', __name__)

# GET  /plans          — 可用计划列表（公开，无需认证）
# GET  /me             — 我的订阅状态 (@jwt_required)
# POST /checkout       — 创建 Checkout Session (@jwt_required)
#                        body: {"tier": "basic", "cycle": "monthly",
#                               "success_url": "...", "cancel_url": "..."}
# POST /webhook        — Stripe Webhook（无需认证，用 Stripe 签名验证）
# POST /cancel         — 取消订阅 (@jwt_required)
# POST /reactivate     — 重新激活 (@jwt_required)
# GET  /usage          — 用量详情 (@jwt_required)
# GET  /invoices       — 发票历史 (@jwt_required)
# POST /portal         — Stripe 客户门户 URL (@jwt_required)
```

**注意**: 对 `@jwt_required` 装饰器的引用——如果 Track A 的装饰器尚不可用，
请自行创建一个简单的 mock 装饰器:

```python
# 临时 mock，Track A 完成后替换
def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        g.current_user = type('User', (), {'id': 1})()  # mock user
        return f(*args, **kwargs)
    return decorated
```

### 6. 自动分配 Free Plan

新用户注册时应自动获得 free plan。实现方式:

- 提供 `SubscriptionService.ensure_subscription(user_id)` 方法
- Track A 的注册路由应在创建用户后调用此方法
- 如果 Track A 不调用，配额检查时自动创建

### 7. 单元测试 (`backend/tests/test_subscriptions.py`)

测试覆盖:

- Plan 配置读取
- 配额检查（允许/拒绝/unlimited）
- 配额扣减
- 功能权限检查
- Stripe Webhook 事件处理（mock stripe 签名）
- 月度配额重置
- 订阅升级/降级

## 验收标准

1. 代码文件已创建且语法正确: `python -m py_compile backend/subscriptions/models.py backend/subscriptions/routes.py backend/subscriptions/stripe_service.py backend/subscriptions/quota_service.py`
2. 导入路径正确: `python -c "from backend.subscriptions.models import Subscription, QuotaUsage, Invoice"`
3. Mock 模式可用: 无 Stripe Key 时不崩溃
4. [可选] 单元测试通过

## 环境说明

- 项目使用 Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: `pip install -r requirements.txt`
- 如果依赖安装失败，跳过测试，直接提交代码
- 验证方式: 语法检查 (`python -m py_compile`) 优先于测试
