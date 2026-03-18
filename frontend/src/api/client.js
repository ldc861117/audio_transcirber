import axios from "axios";

// Local API base (always empty for relative URLs → same origin in web, localhost in desktop)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// Cloud API base for auth/subscriptions (desktop app → Cloud Run, web → same origin)
const CLOUD_API_URL = import.meta.env.VITE_CLOUD_API_URL || API_BASE_URL;

// Local client for transcription, speakers, export (stays on local Flask)
const client = axios.create({
  baseURL: `${API_BASE_URL}/api/v2`,
});

// Cloud client for auth, subscriptions (goes to Cloud Run)
const cloudClient = axios.create({
  baseURL: `${CLOUD_API_URL}/api/v2`,
});

function attachToken(config) {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}

// Attach JWT to both clients
client.interceptors.request.use(attachToken);
cloudClient.interceptors.request.use(attachToken);

// Token refresh logic (shared)
async function handleTokenRefresh(error, axiosInstance) {
  const originalRequest = error.config;

  if (error.response?.status === 401 && !originalRequest._retry) {
    originalRequest._retry = true;

    try {
      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) throw new Error("No refresh token");

      // Always refresh via Cloud client
      const res = await axios.post(`${CLOUD_API_URL}/api/v2/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const newAccessToken = res.data.data.access_token;
      localStorage.setItem("access_token", newAccessToken);
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      return axiosInstance(originalRequest);
    } catch (refreshError) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
      return Promise.reject(refreshError);
    }
  }

  return Promise.reject(error);
}

// Response interceptors
client.interceptors.response.use(
  (response) => response,
  (error) => handleTokenRefresh(error, client),
);
cloudClient.interceptors.response.use(
  (response) => response,
  (error) => handleTokenRefresh(error, cloudClient),
);

export default client;
export { cloudClient };
