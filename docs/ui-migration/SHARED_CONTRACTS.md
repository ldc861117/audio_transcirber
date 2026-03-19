# Le-Trans UI Migration — Shared Contracts

> 所有 Jules 并行 Track 必须遵守的公共契约。实施前必读。

## 1. 品牌标识

- **英文品牌**: Le-Trans
- **中文品牌**: 乐生
- **标语**: AI Audio Studio
- **Logo**: 使用 Material Symbol `graphic_eq` 图标 (Filled) 作为临时 Logo

## 2. CSS Design Tokens

所有颜色、间距、字体必须使用 `frontend/src/styles/variables.css` 中的 CSS 变量。

| Token | Value | 用途 |
|---|---|---|
| `--bg-color` | `#0b1326` | 页面背景 |
| `--bg-secondary` | `#131b2e` | 卡片/面板背景 |
| `--bg-tertiary` | `#171f33` | 输入框/嵌套容器 |
| `--bg-elevated` | `#222a3d` | 悬浮/弹窗 |
| `--accent-primary` | `#d0bcff` | 主色 (Violet) |
| `--accent-secondary` | `#a078ff` | 深紫 |
| `--accent-gradient` | `linear-gradient(135deg, #a078ff, #d0bcff)` | 渐变按钮 |
| `--accent-warm` | `#ffb869` | 暖色强调 |
| `--text-primary` | `#dae2fd` | 主文字 |
| `--text-secondary` | `#cbc3d7` | 次要文字 |
| `--success` | `#10b981` | 成功状态 |
| `--error` | `#ffb4ab` | 错误状态 |
| `--warning` | `#f59e0b` | 警告状态 |
| `--glass-panel` | `rgba(2,6,23,0.7)` | 毛玻璃面板 |
| `--glass-card` | `rgba(34,42,61,0.4)` | 毛玻璃卡片 |
| `--shadow-ai-glow` | `0 0 15px -2px rgba(208,188,255,0.3)` | AI 光效 |
| `--font-headline` | `'Manrope', sans-serif` | 标题/数字 |
| `--font-body` | `'Inter', 'Noto Sans SC', sans-serif` | 正文 |
| `--sidebar-width` | `264px` | Sidebar 展开宽度 |
| `--sidebar-collapsed` | `80px` | Sidebar 折叠宽度 |
| `--border-radius` | `12px` | 标准圆角 |
| `--border-radius-lg` | `20px` | 大圆角 |
| `--border-radius-xl` | `24px` | 超大圆角 |

### ⚠️ 禁止

- ❌ 硬编码任何颜色值 (如 `color: '#3b82f6'`)
- ❌ 硬编码字体 (如 `fontFamily: 'Arial'`)
- ❌ 使用 Tailwind 类名 (项目未安装 Tailwind)

## 3. CSS Utility Classes

以下工具类已在 `global.css` 中定义，可直接使用:

| Class | 用途 |
|---|---|
| `glass-panel` | 毛玻璃面板 (sidebar, header) |
| `glass-card` | 毛玻璃卡片 (列表项, 弹窗) |
| `card` | 标准卡片 (实体背景) |
| `ai-glow` | AI 光效阴影 |
| `font-headline` | 标题字体 |
| `badge` | 基础徽章样式 |
| `badge-primary` / `badge-success` / `badge-warning` / `badge-error` | 彩色徽章 |
| `btn-primary` | 主要按钮 (渐变) |
| `hover-bright` | 悬停提亮 |
| `sidebar-link` | 侧边栏链接 hover |
| `press-effect` | 点击缩放反馈 |

## 4. 共享 UI Primitive 组件

位于 `frontend/src/components/ui/`，通过 barrel export 使用:

```jsx
import { GlassCard, StatusBadge, ProgressRing, MaterialIcon } from '../../components/ui';
```

### GlassCard

```jsx
<GlassCard variant="card" glow={false} onClick={fn} className="custom" style={{}}>
  {children}
</GlassCard>
```

| Prop | Type | Default | 说明 |
|---|---|---|---|
| `variant` | `'panel' \| 'card' \| 'subtle'` | `'card'` | 对应 `glass-panel`, `glass-card`, `glass-subtle` |
| `glow` | `boolean` | `false` | 添加 `ai-glow` 效果 |
| `onClick` | `function` | - | 点击回调 |
| `className` | `string` | - | 额外类名 |
| `style` | `object` | - | 额外样式 |
| `children` | `ReactNode` | - | 子内容 |

### StatusBadge

```jsx
<StatusBadge variant="success">完成</StatusBadge>
```

| Prop | Type | Default | 说明 |
|---|---|---|---|
| `variant` | `'primary' \| 'success' \| 'warning' \| 'error'` | `'primary'` | 颜色变体 |
| `children` | `ReactNode` | - | 内容 |

### ProgressRing

```jsx
<ProgressRing percentage={75} size={48} strokeWidth={4} color="var(--accent-primary)" />
```

### MaterialIcon

```jsx
<MaterialIcon name="graphic_eq" size={24} filled />
```

| Prop | Type | Default | 说明 |
|---|---|---|---|
| `name` | `string` | - | Material Symbol 名称 |
| `size` | `number` | `24` | 像素大小 |
| `filled` | `boolean` | `false` | 是否使用 Filled 变体 |

## 5. 依赖清单 (已安装)

| Package | Version | 用途 |
|---|---|---|
| `react` | `^19.2.0` | UI 框架 |
| `react-router-dom` | `^7.13.1` | 路由 |
| `framer-motion` | `^12.34.3` | 动画 |
| `lucide-react` | `^0.575.0` | 图标 |
| `zustand` | `^5.0.11` | 状态管理 |
| `axios` | `^1.13.5` | HTTP 请求 |

### ⚠️ 禁止

- ❌ 安装新的 npm 包 (如 Tailwind, styled-components 等)
- ❌ 修改 `package.json`

## 6. 只读文件 (所有 Track)

以下文件/目录所有 Track 都**不得修改**:

| Path | 原因 |
|---|---|
| `frontend/src/stores/*` | 状态逻辑不在本次迭代范围 |
| `frontend/src/api/*` | API 接口不变 |
| `frontend/src/App.jsx` | 路由不变 |
| `frontend/src/main.jsx` | 入口不变 (Phase 0 由人工改) |
| `frontend/src/styles/*` | Phase 0 由人工改, Track 不得再改 |
| `frontend/src/components/ui/*` | Phase 0 由人工创建, Track 只读使用 |

## 7. 代码风格

- **Inline styles** 为主 (保持现有风格)，辅以上述 CSS 类
- **组件命名**: PascalCase (如 `GlassCard`)
- **文件命名**: PascalCase.jsx (如 `GlassCard.jsx`)
- **CSS 变量引用**: `var(--token-name)` (在 inline style 中)
- **注释**: 关键逻辑用中文或英文注释均可
- **导入排序**: React → 第三方 → 本地组件 → stores → api
