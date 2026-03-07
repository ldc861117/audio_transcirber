# [V2 Track A] JWT Authentication System

## 目标

将现有 Flask-Login Session 认证替换为 JWT 双 Token (Access + Refresh) 认证系统，
扩展 User 模型支持 email、角色、账户状态。

## 必读

- `docs/tasks/SHARED_CONTRACTS_V2.md` — 完整的共享契约（**最重要**，特别是 Section 3.1, 3.2, 5）
- `auth.py` — 当前认证实现（121 行，Flask-Login + SQLite 直接操作）
- `app.py` — 理解当前认证路由（`/api/auth/*`，第 450-516 行）

## 前置依赖

- **Track E** 的 `backend/db/base.py` 和 `backend/config.py` 必须先存在
- 如果 Track E 尚未完成，请自行创建这些文件（按照 SHARED_CONTRACTS_V2.md 的模板）

## 职责边界

**负责**:

- `backend/auth/__init__.py`
- `backend/auth/models.py` — User + RefreshToken SQLAlchemy 模型
- `backend/auth/jwt_manager.py` — JWT 发放/验证/刷新
- `backend/auth/decorators.py` — `@jwt_required`, `@admin_required`
- `backend/auth/routes.py` — `/api/v2/auth/*` 路由
- `backend/auth/utils.py` — 密码哈希、邮箱验证等工具函数
- `backend/tests/test_auth.py` — 单元测试

**不负责**:

- 订阅/支付逻辑（Track B）
- 转录路由（Track C）
- 前端改造（Track D）

## 子任务

### 1. 创建 User 模型 (`backend/auth/models.py`)

按照 `SHARED_CONTRACTS_V2.md` Section 3.1 创建 User 模型:

- 必须包含 `email`, `role`, `status`, `email_verified`, `last_login_at`
- 包含 `subscription` relationship（定义 relationship，Subscription 模型由 Track B 创建）
- 密码使用 `werkzeug.security.generate_password_hash` / `check_password_hash`
- 提供静态方法: `create()`, `authenticate()`, `get_by_id()`, `get_by_email()`

### 2. 创建 RefreshToken 模型 (`backend/auth/models.py`)

按照 `SHARED_CONTRACTS_V2.md` Section 3.2，用于持久化 refresh token 的 hash:

- `token_hash`: 存储 refresh token 的 SHA-256 hash（不存原文）
- `revoked`: 支持主动撤销
- 提供 `create()`, `find_valid()`, `revoke()`, `revoke_all_for_user()` 方法

### 3. 实现 JWT 管理 (`backend/auth/jwt_manager.py`)

```python
def create_access_token(user) -> str:
    """创建 15 分钟 access token，payload 含 sub, username, role, tier"""

def create_refresh_token(user) -> str:
    """创建 7 天 refresh token，存储 hash 到 DB"""

def verify_access_token(token: str) -> dict | None:
    """验证 access token，返回 payload 或 None"""

def refresh_access_token(refresh_token: str) -> str | None:
    """用 refresh token 换新 access token"""

def revoke_refresh_token(refresh_token: str) -> bool:
    """撤销 refresh token"""
```

使用 `PyJWT` 库，配置从 `backend/config.py` 读取。
Token payload 格式必须严格遵循 `SHARED_CONTRACTS_V2.md` Section 5。

### 4. 实现装饰器 (`backend/auth/decorators.py`)

```python
from functools import wraps
from flask import request, jsonify, g

def jwt_required(f):
    """
    从 Authorization: Bearer <token> 提取并验证 access_token。
    验证通过后将 user 对象注入 g.current_user。
    失败返回 401 + {"error": {"code": "AUTH_REQUIRED" | "TOKEN_EXPIRED" | "TOKEN_INVALID"}}
    """

def admin_required(f):
    """
    先执行 jwt_required，然后检查 g.current_user.role == 'admin'。
    非 admin 返回 403。
    """

def subscription_required(min_tier='basic'):
    """
    检查用户订阅等级 >= min_tier。
    等级顺序: free < basic < pro
    不满足返回 403 + {"error": {"code": "INSUFFICIENT_PLAN"}}
    """
```

### 5. 创建路由 (`backend/auth/routes.py`)

```python
auth_bp = Blueprint('auth', __name__)

# POST /register  — email + username + password → 创建用户 + 返回 tokens
# POST /login     — email/username + password → 返回 tokens
# POST /refresh   — refresh_token → 新 access_token
# POST /logout    — 撤销 refresh_token
# GET  /me        — 返回当前用户信息（含订阅状态）
# PUT  /me        — 更新个人信息（username, email）
# POST /change-password — old_password + new_password
```

**注册逻辑**:

- 验证: email 格式 + username 2-32 字符 + password >= 6 字符
- 检查 email/username 唯一性
- 创建 User（role='user', status='active'）
- 自动创建 free 订阅（如果 Subscription 模型存在的话；否则跳过）
- 返回 access_token + refresh_token + user 信息

**登录逻辑**:

- 支持 email 或 username 登录
- 更新 `last_login_at`
- 返回 access_token + refresh_token + user 信息

所有响应必须遵循 `SHARED_CONTRACTS_V2.md` Section 4.2 的格式。

### 6. 单元测试 (`backend/tests/test_auth.py`)

测试覆盖:

- 注册成功 / 重复 email / 重复 username / 无效输入
- 登录成功 / 错误密码 / 不存在的用户
- Token 验证 / 过期 token
- Refresh token 刷新 / 撤销
- `@jwt_required` 装饰器
- `@admin_required` 装饰器
- 修改密码

## 验收标准

1. 代码文件已创建且语法正确: `python -m py_compile backend/auth/models.py backend/auth/jwt_manager.py backend/auth/routes.py backend/auth/decorators.py`
2. 导入路径正确: `python -c "from backend.auth.models import User, RefreshToken"`
3. [可选] 单元测试通过: `python -m pytest backend/tests/test_auth.py -v`

## 环境说明

- 项目使用 Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: `pip install -r requirements.txt`
- 如果依赖安装失败，跳过测试，直接提交代码
- 验证方式: 语法检查 (`python -m py_compile`) 优先于测试
