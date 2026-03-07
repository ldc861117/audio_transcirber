# [V2 Track E] Infrastructure & Database Foundation

## 目标

创建项目的基础设施层：Flask 应用工厂、SQLAlchemy ORM 基础、环境配置管理。
此 Track 的产出是其他所有 Track 的基础依赖。

## 必读

- `docs/tasks/SHARED_CONTRACTS_V2.md` — 完整的共享契约（**最重要**）
- `app.py` — 当前的 Flask 应用（理解现有结构）
- `requirements.txt` — 当前依赖
- `.env.example` — 当前环境变量

## 职责边界

**负责**:

- `backend/config.py` — 环境配置
- `backend/extensions.py` — Flask 扩展初始化
- `backend/db/base.py` — SQLAlchemy Base + init
- `backend/db/__init__.py`
- `backend/__init__.py`
- `backend/requirements.txt` — 后端依赖更新
- `.env.example` — 环境变量模板更新

**不负责**:

- 具体的业务模型（由各 Track 各自创建）
- 路由和业务逻辑
- 前端代码

## 子任务

### 1. 创建后端包结构

```bash
mkdir -p backend/db
touch backend/__init__.py
touch backend/db/__init__.py
```

### 2. 创建 `backend/config.py`

按照 `SHARED_CONTRACTS_V2.md` Section 9 的模板创建，支持:

- `DevelopmentConfig` (SQLite, DEBUG=True)
- `ProductionConfig` (DATABASE_URL from env, DEBUG=False)
- 所有环境变量从 `.env` 读取

### 3. 创建 `backend/extensions.py`

按照 `SHARED_CONTRACTS_V2.md` Section 8 的模板创建:

- `cors` 实例
- `init_extensions(app)` 函数

### 4. 创建 `backend/db/base.py`

按照 `SHARED_CONTRACTS_V2.md` Section 7 的模板创建:

- `db = SQLAlchemy()` 实例
- `init_db(app)` 函数

### 5. 更新依赖

在根目录 `requirements.txt` 中**追加**（不要删除现有依赖）:

```
flask-sqlalchemy>=3.1
alembic>=1.13
PyJWT>=2.8
stripe>=8.0
```

### 6. 更新 `.env.example`

在现有内容基础上**追加**:

```bash
# === V2 New Variables ===
# JWT
JWT_SECRET_KEY=change-me-to-random-string
JWT_REFRESH_SECRET_KEY=change-me-to-different-random-string

# Stripe (test mode)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# Database (optional, defaults to SQLite)
# DATABASE_URL=postgresql://user:pass@localhost/audio_transcriber

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5099
```

## 验收标准

1. `python -c "from backend.config import configs; print(configs)"` — 成功导入
2. `python -c "from backend.db.base import db; print(db)"` — 成功导入
3. `python -c "from backend.extensions import cors; print(cors)"` — 成功导入
4. 新的依赖能正常安装: `pip install flask-sqlalchemy alembic PyJWT stripe`
5. 不破坏现有 `app.py` 的功能（不修改现有代码）

## 环境说明

- 项目使用 Python 3.11+，依赖在 requirements.txt
- 如需运行测试，先执行: `pip install -r requirements.txt`
- 如果依赖安装失败，跳过测试，直接提交代码
- 验证方式: 语法检查 (`python -m py_compile`) 优先于测试
