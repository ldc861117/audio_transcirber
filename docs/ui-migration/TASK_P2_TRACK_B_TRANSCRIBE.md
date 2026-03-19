# [Phase 2 Track B] Transcribe 页面升级

## 目标
将 Transcribe 从线性纵向堆叠改为 Bento 双列布局 + Stats Bar + Log Console。

## 必读
- `docs/ui-migration/SHARED_CONTRACTS.md` (共享契约, **必须首先阅读**)
- `docs/ui-designed-by-stitch/code.md` (Stitch 设计参考, 搜索 "Transcribe" 页面 HTML)
- `frontend/src/pages/Transcribe/Transcribe.jsx` (当前实现, 全部逻辑保留)
- `frontend/src/components/Progress/PipelineTimeline.jsx` (当前 pipeline 组件)
- `frontend/src/components/Progress/EventLog.jsx` (当前日志组件)
- `frontend/src/components/Recorder/Recorder.jsx` (录音组件, 保留)
- `frontend/src/components/Transcript/TranscriptView.jsx` (转写结果, 保留)
- `frontend/src/components/Transcript/ExportPanel.jsx` (导出面板, 保留)

## 子任务

### 1. 修改 `frontend/src/pages/Transcribe/Transcribe.jsx`

保留**所有**现有状态逻辑 (file, uploading, taskId, taskData, error, polling)。仅修改 JSX 渲染结构。

#### 上半区: Bento 双列 (上传 + ongoing)

```
grid: 2fr 1fr, gap: 1.5rem
```

**左列: Drop Zone**
- `GlassCard variant="card"`, min-height: 360px
- 居中: Upload 图标 (64px, text-secondary)
- 主文案: "拖拽音频文件到此处" (font-headline, 1.1rem)
- 副文案: "或点击选择文件 · 支持 MP3, WAV, M4A, FLAC" (text-secondary, 0.85rem)
- 选中文件后: 显示文件名 + 大小 + "点击更换"
- border: `2px dashed rgba(255,255,255,0.1)`, hover 变为 `var(--accent-primary)`
- Recorder 组件放在 Drop Zone 下方

**右列: Ongoing Tasks 面板**
- `GlassCard variant="card"`, 标题 "进行中的任务"
- 当 `isActive=true` 时显示:
  - 垂直步骤列表 (替代水平 PipelineTimeline):
    - 每步: 图标 + 阶段名 + 状态指示 (✅ Done / 🔄 Active spinner / ⏳ Pending dimmed)
    - 参考现有 `PipelineTimeline` 的 `STAGES` 数组和 `getStageState` 逻辑
  - 底部: 总进度百分比 + 进度条 (ai-glow 效果)
- 当无任务时: 显示 "暂无进行中任务" placeholder

**Options strip** (保留现有, 样式微调):
- Provider + Model 显示
- 说话人识别开关
- 开始转写按钮 (btn-primary class)

#### 中间: Stats Bar (4列, 仅在 isActive 或 isDone 时显示)

```jsx
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
  <GlassCard variant="card" style={{ padding: '1rem', textAlign: 'center' }}>
    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>耗时</div>
    <div style={{ fontFamily: 'var(--font-headline)', fontSize: '1.5rem', fontWeight: 700 }}>
      {formatElapsed()}
    </div>
  </GlassCard>
  {/* Words Detected */}
  {/* Speakers Found */}
  {/* Chunks */}
</div>
```

Stats 数据来源 (从 `taskData` 取):
| Stat | 数据 | 单位 |
|---|---|---|
| 耗时 | `taskData.elapsed_seconds` | 格式化为 Xm Ys |
| 字数 | `taskData.transcript?.length` | 字 |
| 说话人 | `taskData.speakers?.length` | 人 |
| 分段 | `taskData.completed_chunks / taskData.total_chunks` | 段 |

#### 下方: Developer Log Console

重构 EventLog 的渲染方式 (在 Transcribe.jsx 内部, 不修改 EventLog 组件本身):

- 固定在页面内容底部, `glass-card` 背景
- 标题栏: `Terminal` 图标 + "Developer Log" + 折叠/展开按钮
- monospace 字体, 深色背景 `rgba(0,0,0,0.3)`
- 时间戳 + 阶段 Badge + 消息
- 可以直接复用 `<EventLog>` 组件, 只调整外部容器样式

#### 结果区域

保持现有 `TranscriptView` + `ExportPanel`，外层包裹 `GlassCard`:
```jsx
{isDone && (
  <GlassCard variant="card" style={{ padding: '2rem', marginTop: '1.5rem' }}>
    {/* 完成标题 + TranscriptView + ExportPanel */}
  </GlassCard>
)}
```

### 2. 保留所有业务逻辑
- file 状态管理、upload、polling 全部原封不动
- 只改 JSX 结构和样式, 不改逻辑

## 导入
```jsx
import { GlassCard, StatusBadge, MaterialIcon } from '../../components/ui';
```

## 不负责
- ❌ 不修改 `PipelineTimeline.jsx` (在 Transcribe.jsx 中重新实现垂直版本)
- ❌ 不修改 `EventLog.jsx` (只调整外部容器)
- ❌ 不修改 Layout/Sidebar/Header
- ❌ 不修改任何 store 或 API
- ❌ 不修改 styles/ 目录
- ❌ 不安装新包

## 验收标准
1. `npm run build` 无错误
2. 双列布局: 左 Drop Zone + 右 Ongoing Tasks
3. Stats Bar 在有任务数据时显示 4 个统计卡片
4. Developer Log 在底部, 可折叠
5. 文件上传功能正常 (逻辑不变)
6. 完成后显示 TranscriptView + ExportPanel
7. 无硬编码颜色

## 环境说明
- 项目使用 Vite + React 19, 无 Tailwind
- 共享 UI 组件在 `frontend/src/components/ui/`
- 如需运行 build: `cd frontend && npm install && npm run build`
