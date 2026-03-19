# [Phase 1 Track A] Sidebar 重构 — Le-Trans 品牌升级

## 目标
将 Sidebar 从简单导航列表升级为 4 区域布局: Brand / Nav / Quota / Profile。

## 必读
- `docs/ui-migration/SHARED_CONTRACTS.md` (共享契约, **必须首先阅读**)
- `docs/ui-designed-by-stitch/code.md` (Stitch 设计参考, 搜索 "sidebar" 和 "nav-link" 相关 HTML)
- `frontend/src/components/Layout/Sidebar.jsx` (当前实现)
- `frontend/src/components/QuotaBar/QuotaBar.jsx` (Quota 逻辑参考)
- `frontend/src/stores/subscriptionStore.js` (订阅数据源, 只读)
- `frontend/src/stores/authStore.js` (用户数据源, 只读)

## 子任务

### 1. 重写 `frontend/src/components/Layout/Sidebar.jsx`

将组件重构为 4 个区域:

#### Zone 1: Brand
- Logo: 使用 `MaterialIcon` 组件 `<MaterialIcon name="graphic_eq" size={32} filled />`
- 标题: "Le-Trans" (font-headline, 渐变文字)
- 副标题: "AI Audio Studio" (font-size: 0.65rem, text-secondary, uppercase, tracking-widest)

#### Zone 2: Navigation
保留现有 7 个 NavLink 路由:
| Route | 图标 (Lucide) | 标签 |
|---|---|---|
| `/` | `LayoutDashboard` | 仪表盘 |
| `/transcribe` | `FileAudio` | 新转写 |
| `/history` | `History` | 历史记录 |
| `/speakers` | `Users` | 声纹库 |
| `/pricing` | `CreditCard` | 定价方案 |
| `/account` | `UserCircle` | 账户管理 |
| `/settings` | `Settings` | 设置 |

Active 样式:
```jsx
backgroundColor: 'rgba(160,120,255,0.1)',
borderLeft: '3px solid var(--accent-primary)',
color: 'var(--text-primary)',
```

#### Zone 3: Quota + Upgrade CTA
- 从 `useSubscriptionStore` 获取 `usage` 和 `subscription` 数据
- 渲染 `ProgressRing` 或水平进度条
- 文字: `已用 X / Y 分` 或 `配额: ∞` (Pro)
- "升级" 按钮: Link to `/pricing`, 使用 `btn-primary` 样式, 全宽

#### Zone 4: User Profile
- 从 `useAuthStore` 获取 `user.username`
- 圆形头像占位 (首字母), 如 `<div>D</div>` styled as circle
- 名称 + 角色 Badge (使用 `StatusBadge`), 如 `<StatusBadge variant="primary">Pro</StatusBadge>`

### 2. 整体样式
- 固定宽度: `var(--sidebar-width)` = 264px
- 折叠宽度: `var(--sidebar-collapsed)` = 80px
- 背景: `glass-panel` class
- 保留 `framer-motion` 展开/折叠动画
- `overflow-x: hidden`
- 各区域间用 `border-bottom: 1px solid rgba(255,255,255,0.05)` 分隔

### 3. 导入新组件
```jsx
import { GlassCard, StatusBadge, ProgressRing, MaterialIcon } from '../../components/ui';
```

## 不负责
- ❌ 不修改 Header.jsx
- ❌ 不修改 Layout.jsx
- ❌ 不修改任何 store 或 API
- ❌ 不修改 styles/ 目录
- ❌ 不安装新包

## 验收标准
1. `npm run build` 无错误
2. Sidebar 展开时显示 4 个区域 (Brand/Nav/Quota/Profile)
3. Sidebar 折叠时只显示图标
4. 导航 active 状态有紫色高亮
5. Quota 数据正确显示 (从 subscriptionStore 读取)
6. 用户名正确显示 (从 authStore 读取)
7. 代码使用 CSS 变量, 无硬编码颜色

## 环境说明
- 项目使用 Vite + React 19
- 如需运行 `npm run build`, 先 `cd frontend && npm install`
- 如依赖安装失败, 跳过 build, 直接确认语法正确
