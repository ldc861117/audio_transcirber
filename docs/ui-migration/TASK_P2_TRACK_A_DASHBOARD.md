# [Phase 2 Track A] Dashboard 升级

## 目标
将 Dashboard 从 2 列栅格升级为 3 区域 Bento 布局: Welcome Banner + Quick Actions + Recent Transcripts。

## 必读
- `docs/ui-migration/SHARED_CONTRACTS.md` (共享契约, **必须首先阅读**)
- `docs/ui-designed-by-stitch/code.md` (Stitch 设计参考, 搜索 "Dashboard" 页面的 HTML)
- `frontend/src/pages/Dashboard/Dashboard.jsx` (当前实现)
- `frontend/src/stores/authStore.js` (用户数据, 只读)
- `frontend/src/api/endpoints.js` (API 接口, 只读)

## 子任务

### 1. 重写 `frontend/src/pages/Dashboard/Dashboard.jsx`

#### Zone 1: Welcome Banner
- 全宽渐变背景: `background: linear-gradient(135deg, rgba(160,120,255,0.15), rgba(255,184,105,0.08))`
- 圆角 `var(--border-radius-xl)`, padding `2.5rem`
- 标题: `Good morning, {user.username}.` (font-headline, 1.75rem, bold)
- 副标题: 根据 recentTasks length 动态显示 "你有 N 个正在进行的任务。" 或 "今天想转写些什么？"
- 右侧: 装饰性 blur 光球 (position: absolute, 不需要交互)

#### Zone 2: Bento Quick Actions (3列)
使用 `GlassCard` 组件, 3 列 grid:

| 卡片 | 图标 | 标题 | 副文案 | 点击行为 |
|---|---|---|---|---|
| 新录音 | `Mic` (Lucide) | 新录音 | 使用内置录音机 | `navigate('/transcribe')` |
| 上传文件 | `Upload` (Lucide) | 上传音频 | 拖拽至转写页面 | `navigate('/transcribe')` |
| 统计概览 | `BarChart3` (Lucide) | 本月数据 | 显示本月已用分钟数 | `navigate('/account')` |

每个卡片:
- `GlassCard variant="card"`, cursor pointer
- 图标在上 (48px icon 区域, accent 颜色), 标题 + 副文案在下
- hover: `transform: translateY(-2px)`, `box-shadow: var(--shadow-ai-glow)`

#### Zone 3: Recent Transcripts
- 标题: "最近转写" + "查看全部" link (→ `/history`)
- 每个任务渲染为 `GlassCard variant="card"`:
  - 文件名 (font-headline, truncate)
  - 时间 (text-secondary, 0.75rem)
  - `StatusBadge` 显示状态 (done=success, error=error, 其他=primary)
  - 点击: `navigate('/history?task=' + task.id)`
- 空状态: 居中图标 + "暂无转写记录" 文字
- Loading: Loader2 + "加载中..."

### 2. 保留现有数据逻辑
- `api.transcriptions.list({ per_page: 5, page: 1 })` 数据获取
- `useAuthStore()` 用户信息

### 3. 删除 "使用小贴士" 区域
Tips 区域在 Stitch 设计中不存在，删除该部分。

## 导入
```jsx
import { GlassCard, StatusBadge, MaterialIcon } from '../../components/ui';
```

## 不负责
- ❌ 不修改 Layout/Sidebar/Header
- ❌ 不修改任何 store 或 API
- ❌ 不修改 styles/ 目录
- ❌ 不安装新包

## 验收标准
1. `npm run build` 无错误
2. Welcome Banner 有渐变背景 + 用户名
3. 3 列 Bento 卡片, 点击跳转正确
4. Recent Transcripts 使用 GlassCard + StatusBadge
5. 空状态显示正确
6. 无硬编码颜色

## 环境说明
- 项目使用 Vite + React 19, 无 Tailwind
- 共享 UI 组件在 `frontend/src/components/ui/`
- 如需运行 build: `cd frontend && npm install && npm run build`
