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
