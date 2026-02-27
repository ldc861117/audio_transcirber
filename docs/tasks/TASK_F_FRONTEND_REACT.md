# [Phase1 Track F] React + Vite 前端基础搭建

## 目标

使用 React + Vite 搭建前端工程化基础，实现 Dashboard 和 Transcribe 两个核心页面，代理到现有 Flask 后端。

## 必读文档

- `contracts.yaml` — 理解后端 API 数据结构
- `static/app.js` — 现有前端逻辑（用于理解功能，但不复制代码风格）
- `static/index.html` — 现有 UI 布局参考
- `app.py` — 后端 API 端点列表
- `AGENTS.md` — 开发规范

## ⚠️ 严格文件边界

**只能创建/修改：** `frontend/` 目录下的所有内容

**绝不修改：**

- `app.py`, `auth.py`, `speaker.py`, `speaker_db.py`
- `static/*` — 保持原前端完整可用
- `contracts.yaml`

## 子任务

### 1. 项目初始化

```bash
cd /path/to/audio-transcriber
npx -y create-vite frontend --template react
cd frontend
npm install
npm install axios react-router-dom zustand
```

### 2. 项目结构

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js           # axios instance with interceptors
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Header.jsx      # 顶部导航 (品牌 + 用户信息)
│   │   │   ├── Sidebar.jsx     # 侧栏导航
│   │   │   └── Layout.jsx      # 主布局 wrapper
│   │   ├── AudioUpload/
│   │   │   ├── DropZone.jsx    # 拖拽上传区
│   │   │   └── FileInfo.jsx    # 文件信息显示
│   │   ├── Progress/
│   │   │   ├── ProgressBar.jsx # 转写进度条
│   │   │   └── ChunkGrid.jsx  # chunk 进度网格
│   │   └── Auth/
│   │       └── ProtectedRoute.jsx
│   ├── pages/
│   │   ├── Dashboard/
│   │   │   └── Dashboard.jsx   # 仪表盘：最近任务 + 快速操作
│   │   ├── Transcribe/
│   │   │   └── Transcribe.jsx  # 新建转写页
│   │   ├── History/
│   │   │   └── History.jsx     # 历史列表（预留，可用 placeholder）
│   │   ├── Speakers/
│   │   │   └── Speakers.jsx    # 声纹库（预留，可用 placeholder）
│   │   ├── Settings/
│   │   │   └── Settings.jsx    # 设置页：API 配置
│   │   └── Login/
│   │       ├── Login.jsx
│   │       └── Register.jsx
│   ├── stores/
│   │   ├── authStore.js        # 认证状态
│   │   └── transcribeStore.js  # 转写状态
│   ├── hooks/
│   │   └── usePolling.js       # 轮询 hook
│   ├── styles/
│   │   ├── global.css          # 全局样式 + CSS 变量
│   │   └── variables.css       # 设计 token
│   ├── App.jsx                 # 路由定义
│   └── main.jsx
├── vite.config.js
├── package.json
└── index.html
```

### 3. Vite 代理配置 — `vite.config.js`

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:5099",
        changeOrigin: true,
      },
    },
  },
});
```

### 4. API Client — `src/api/client.js`

- axios 实例，baseURL 为 `/api`
- 请求拦截器：附加认证 headers
- 响应拦截器：401 时跳转登录
- 封装方法：
  ```javascript
  export const api = {
    auth: {
      login: (data) => client.post("/auth/login", data),
      register: (data) => client.post("/auth/register", data),
      logout: () => client.post("/auth/logout"),
      me: () => client.get("/auth/me"),
    },
    transcriptions: {
      upload: (formData) => client.post("/upload", formData),
      status: (taskId) => client.get(`/status/${taskId}`),
    },
    providers: {
      list: () => client.get("/builtin-providers"),
      test: (data) => client.post("/test-connection", data),
    },
  };
  ```

### 5. 核心页面实现

#### Dashboard (`pages/Dashboard/Dashboard.jsx`)

- 欢迎信息 + 用户名
- "快速转写" 快捷按钮 → 导航到 /transcribe
- 最近任务列表（调用现有 API，或 placeholder）
- 简洁、现代设计

#### Transcribe (`pages/Transcribe/Transcribe.jsx`)

- Provider 选择（Gemini / 智谱 / ModelScope / 自定义）
- API 配置区域（与现有 configPanel 功能对应）
- 音频上传 Drop Zone
- 转写进度实时显示
- 结果展示 + 复制/下载

### 6. 设计风格

- **配色**：深色主题优先，辅以亮色 accent
- **字体**：使用 Inter 或 Noto Sans SC
- **组件**：圆角卡片、微动画、渐变按钮
- **响应式**：支持桌面和平板

## 验收标准

1. `cd frontend && npm run build` 成功
2. `cd frontend && npm run dev` 启动后能访问 http://localhost:3000
3. 登录页功能正常（代理到 Flask 后端）
4. Dashboard 页面可渲染
5. Transcribe 页面可上传文件并展示进度

## 注意事项

- 前端通过 Vite proxy 连接到 Flask 后端 (localhost:5099)
- 不要修改任何后端文件
- History / Speakers / Settings 页面可以是 placeholder（显示"即将推出"）
- 保持 `static/` 目录原前端完整可用，新旧前端可共存

## 环境说明

- Node.js 18+, npm 9+
- 如果 npm install 失败，检查 Node 版本
- 验证方式: `npm run build` 优先于开发服务器测试
