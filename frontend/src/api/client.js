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

        // 使用原生 axios 避免拦截器循环
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
