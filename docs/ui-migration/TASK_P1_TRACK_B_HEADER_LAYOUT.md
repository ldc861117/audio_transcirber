# [Phase 1 Track B] Header 轻量化 + Layout 适配

## 目标
将 Header 从 Logo + QuotaBar 模式改为轻量上下文栏 (Logo 和 Quota 已移至 Sidebar)。同步调整 Layout.jsx 容器参数。

## 必读
- `docs/ui-migration/SHARED_CONTRACTS.md` (共享契约, **必须首先阅读**)
- `docs/ui-designed-by-stitch/code.md` (Stitch 设计参考, 搜索 "top-nav" 相关 HTML)
- `frontend/src/components/Layout/Header.jsx` (当前实现)
- `frontend/src/components/Layout/Layout.jsx` (当前实现)

## 子任务

### 1. 修改 `frontend/src/components/Layout/Header.jsx`

**移除**:
- Logo 文字 "AudioTranscriber" (已移至 Sidebar)
- `<QuotaBar />` 组件引用 (已移至 Sidebar)
- `import QuotaBar from '../QuotaBar/QuotaBar'` 导入

**新增**:
- 左侧: 面包屑 (显示当前页面名, 从 `react-router-dom` 的 `useLocation` 获取)

```jsx
const ROUTE_NAMES = {
  '/': '仪表盘',
  '/transcribe': '新转写',
  '/history': '历史记录',
  '/speakers': '声纹库',
  '/pricing': '定价方案',
  '/account': '账户管理',
  '/settings': '设置',
};
```

- 中间: 搜索框 (UI only, 纯前端样式, 不需要实际搜索功能)

```jsx
<div style={{
  display: 'flex', alignItems: 'center', gap: '0.5rem',
  backgroundColor: 'var(--bg-tertiary)', borderRadius: '999px',
  padding: '0.5rem 1rem', maxWidth: '320px', flex: 1,
}}>
  <Search size={16} style={{ color: 'var(--text-secondary)' }} />
  <span style={{ color: 'var(--text-disabled)', fontSize: '0.85rem' }}>搜索...</span>
</div>
```

- 右侧: 通知图标 (Lucide `Bell`, placeholder) + 帮助图标 (Lucide `HelpCircle`, placeholder) + 用户头像 (首字母圆形) + 退出按钮

**背景样式**:
```jsx
backgroundColor: 'var(--glass-panel)',
backdropFilter: 'blur(12px)',
borderBottom: '1px solid rgba(255,255,255,0.05)',
```

### 2. 修改 `frontend/src/components/Layout/Layout.jsx`

- `main` 区域 padding: 桌面 `2.5rem`, 移动端 `1rem`
- `main` 区域添加 `max-width: 1200px; margin: 0 auto` (居中内容)
- Sidebar 展开时 main 推移: `marginLeft: var(--sidebar-width)`
- 确保 `min-height: 100vh` 和 `background-color: var(--bg-color)` 在最外层

## 不负责
- ❌ 不修改 Sidebar.jsx (Track A 负责)
- ❌ 不修改任何 page 组件
- ❌ 不修改任何 store 或 API
- ❌ 不修改 styles/ 目录
- ❌ 不安装新包

## 验收标准
1. `npm run build` 无错误
2. Header 不再显示 Logo 和 QuotaBar
3. Header 显示当前页面名称 (面包屑)
4. Header 有搜索框 UI (不需要功能)
5. Header 有用户头像 + 退出按钮
6. Header 使用毛玻璃背景
7. Layout main content 居中且有合理 padding
8. 无硬编码颜色

## 环境说明
- 项目使用 Vite + React 19
- 如需运行 `npm run build`, 先 `cd frontend && npm install`
- 如依赖安装失败, 跳过 build, 直接确认语法正确
