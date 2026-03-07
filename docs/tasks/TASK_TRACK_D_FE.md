# [V2 Track D] Frontend Independence & Subscription UI

## 目标

将前端改造为完全独立运行的 SPA，使用 JWT 认证替代 Cookie Session，
新增定价页、账户管理页和配额显示组件。

## 必读

- `docs/tasks/SHARED_CONTRACTS_V2.md` — 完整的共享契约（**最重要**，特别是 Section 4, 5, 6）
- `frontend/src/api/client.js` — 当前 API Client（axios）
- `frontend/src/stores/authStore.js` — 当前认证 Store（Zustand）
- `frontend/src/App.jsx` — 路由结构
- `frontend/package.json` — 依赖列表
- `frontend/vite.config.js` — Vite 配置（当前 build 到 `../static`）

## 职责边界

**负责**:

- `frontend/src/api/client.js` — JWT Token 管理
- `frontend/src/api/endpoints.js` — [NEW] v2 API 端点定义
- `frontend/src/stores/authStore.js` — JWT 登录/刷新
- `frontend/src/stores/subscriptionStore.js` — [NEW] 订阅状态管理
- `frontend/src/pages/Pricing/` — [NEW] 定价页
- `frontend/src/pages/Account/` — [NEW] 账户管理页
- `frontend/src/components/Subscription/` — [NEW] 订阅组件
- `frontend/src/components/QuotaBar/` — [NEW] 配额条组件
- `frontend/vite.config.js` — 独立部署配置
- `frontend/src/App.jsx` — 路由更新

**不负责**:

- 后端 API 实现
- 数据库模型
- 现有功能页面的核心逻辑（Transcribe, History, Speakers, Settings 保持不动）

## 子任务

### 1. API Client JWT 改造 (`frontend/src/api/client.js`)

**替换现有的 Cookie 认证为 JWT Bearer Token**:

```javascript
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v2`,
});

// Request interceptor: 附加 JWT
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: 自动刷新 Token
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const res = await axios.post(`${API_BASE_URL}/api/v2/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccessToken = res.data.data.access_token;
        localStorage.setItem("access_token", newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return client(originalRequest);
      } catch (refreshError) {
        // Refresh 失败 → 清除 tokens → 跳转登录
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export default client;
```

### 2. API 端点定义 (`frontend/src/api/endpoints.js`)

```javascript
import client from "./client";

export const api = {
  auth: {
    register: (data) => client.post("/auth/register", data),
    login: (data) => client.post("/auth/login", data),
    refresh: (data) => client.post("/auth/refresh", data),
    logout: () => client.post("/auth/logout"),
    me: () => client.get("/auth/me"),
    updateProfile: (data) => client.put("/auth/me", data),
    changePassword: (data) => client.post("/auth/change-password", data),
  },
  subscriptions: {
    plans: () => client.get("/subscriptions/plans"),
    me: () => client.get("/subscriptions/me"),
    checkout: (data) => client.post("/subscriptions/checkout", data),
    cancel: () => client.post("/subscriptions/cancel"),
    reactivate: () => client.post("/subscriptions/reactivate"),
    usage: () => client.get("/subscriptions/usage"),
    invoices: () => client.get("/subscriptions/invoices"),
    portal: (data) => client.post("/subscriptions/portal", data),
  },
  transcriptions: {
    upload: (formData) =>
      client.post("/transcriptions/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }),
    status: (taskId) => client.get(`/transcriptions/${taskId}`),
    list: (params = {}) => client.get("/transcriptions/", { params }),
    delete: (taskId) => client.delete(`/transcriptions/${taskId}`),
    updateSpeakers: (taskId, data) =>
      client.post(`/transcriptions/${taskId}/speakers`, data),
    providers: () => client.get("/transcriptions/providers"),
    testConnection: (data) =>
      client.post("/transcriptions/test-connection", data),
  },
  speakers: {
    list: () => client.get("/speakers/"),
    rename: (id, name) => client.post(`/speakers/${id}/name`, { name }),
    delete: (id) => client.delete(`/speakers/${id}`),
    merge: (keepId, mergeId) =>
      client.post("/speakers/merge", { keep_id: keepId, merge_id: mergeId }),
  },
  exports: {
    download: (taskId, format) =>
      client.get(`/export/${taskId}`, {
        params: { format },
        responseType: "blob",
      }),
  },
};
```

### 3. Auth Store JWT 管理 (`frontend/src/stores/authStore.js`)

**替换现有的 Cookie Session 检查为 JWT Token 管理**:

```javascript
import { create } from "zustand";
import { api } from "../api/endpoints";

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  // 初始化：检查 localStorage 中是否有有效 token
  checkAuth: async () => {
    set({ isLoading: true });
    const token = localStorage.getItem("access_token");
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }
    try {
      const res = await api.auth.me();
      set({ user: res.data.data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (credentials) => {
    const res = await api.auth.login(credentials);
    const { access_token, refresh_token, user } = res.data.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    set({ user, isAuthenticated: true });
    return user;
  },

  register: async (data) => {
    const res = await api.auth.register(data);
    const { access_token, refresh_token, user } = res.data.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    set({ user, isAuthenticated: true });
    return user;
  },

  logout: async () => {
    try {
      await api.auth.logout();
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ user: null, isAuthenticated: false });
    }
  },
}));
```

### 4. Subscription Store (`frontend/src/stores/subscriptionStore.js`)

```javascript
import { create } from "zustand";
import { api } from "../api/endpoints";

export const useSubscriptionStore = create((set) => ({
  subscription: null,
  plans: [],
  usage: null,
  invoices: [],
  isLoading: false,

  fetchSubscription: async () => {
    set({ isLoading: true });
    try {
      const res = await api.subscriptions.me();
      set({ subscription: res.data.data, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchPlans: async () => {
    const res = await api.subscriptions.plans();
    set({ plans: res.data.data });
  },

  fetchUsage: async () => {
    const res = await api.subscriptions.usage();
    set({ usage: res.data.data });
  },

  fetchInvoices: async () => {
    const res = await api.subscriptions.invoices();
    set({ invoices: res.data.data });
  },

  checkout: async (tier, cycle) => {
    const res = await api.subscriptions.checkout({
      tier,
      cycle,
      success_url: `${window.location.origin}/account?checkout=success`,
      cancel_url: `${window.location.origin}/pricing?checkout=cancelled`,
    });
    // Redirect to Stripe Checkout
    window.location.href = res.data.data.checkout_url;
  },

  cancelSubscription: async () => {
    await api.subscriptions.cancel();
  },
}));
```

### 5. Pricing 定价页 (`frontend/src/pages/Pricing/Pricing.jsx`)

创建定价对比页面:

- 展示 free, basic, pro 三个 Plan 的对比卡片
- 月付/年付切换
- 当前 Plan 高亮标记
- "升级" 按钮触发 Stripe Checkout
- 免费版显示 "当前方案"
- 美观的卡片式设计，符合项目现有深色风格

参考设计要素:

- 3 列对比卡片
- Pro 卡片带 "推荐" 标签
- 功能列表用 ✓/✗ 标记
- 价格醒目显示（年付显示节省百分比）

### 6. Account 账户页 (`frontend/src/pages/Account/Account.jsx`)

创建账户管理页面，包含 3 个 Tab:

- **个人信息**: username, email, 修改密码
- **订阅管理**: 当前 Plan, 用量进度条, 升级/取消/管理按钮
- **用量历史**: 表格显示历史转录任务的分钟消耗

### 7. QuotaBar 组件 (`frontend/src/components/QuotaBar/QuotaBar.jsx`)

全局配额显示条，嵌入 Layout 顶栏:

- 显示 "已用 X / Y 分钟"
- 进度条颜色: 绿 (< 60%) → 黄 (60-90%) → 红 (> 90%)
- 点击跳转到账户页
- Pro (unlimited) 显示 "∞"

### 8. 路由更新 (`frontend/src/App.jsx`)

添加新路由:

```jsx
<Route path="/pricing" element={<Pricing />} />  {/* 公开，无需登录 */}
<Route element={<ProtectedRoute />}>
  {/* ...现有路由... */}
  <Route path="/account" element={<Account />} />
</Route>
```

### 9. Login/Register 页面更新

- 注册页增加 email 字段
- 登录支持 email 或 username
- 登录/注册成功后存储 JWT tokens

### 10. Vite 配置更新 (`frontend/vite.config.js`)

```javascript
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist", // 不再输出到 ../static
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:5099",
        changeOrigin: true,
      },
    },
  },
});
```

### 11. Layout Sidebar 更新

在侧边栏添加:

- "定价" 菜单项（链接到 /pricing）
- "账户" 菜单项（链接到 /account）
- 底部显示当前 Plan 标签 (如 "FREE" / "PRO")

## 样式要求

- 继续使用项目现有的 **Vanilla CSS** + CSS Variables 暗色主题
- 新组件的 CSS 文件放在组件目录中（如 `Pricing/Pricing.css`）
- 使用现有的 CSS variables（查看 `frontend/src/styles/global.css`）
- 动画使用 `framer-motion`（已有依赖）

## 验收标准

1. `cd frontend && npm run build` — 构建成功无错误
2. 新页面（Pricing, Account）在路由中可访问
3. API Client 使用 JWT Bearer Token
4. authStore 使用 localStorage 存储/读取 tokens
5. subscriptionStore 能正确定义所有 API 调用
6. QuotaBar 组件基本渲染（即使后端未就绪，也不应崩溃 — 优雅降级）

## 环境说明

- 前端使用 React 19 + Vite 7，依赖在 frontend/package.json
- 如需安装依赖: `cd frontend && npm install`
- 构建验证: `cd frontend && npm run build`
- 开发模式: `cd frontend && npm run dev`
