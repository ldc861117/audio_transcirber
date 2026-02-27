import { create } from 'zustand';
import { api } from '../api/client';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  
  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const res = await api.auth.me();
      set({ user: res.data, isAuthenticated: true, isLoading: false });
    } catch (err) {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
  
  login: async (credentials) => {
    const res = await api.auth.login(credentials);
    set({ user: { username: res.data.username }, isAuthenticated: true });
    return res.data;
  },
  
  register: async (data) => {
    const res = await api.auth.register(data);
    set({ user: { username: res.data.username }, isAuthenticated: true });
    return res.data;
  },
  
  logout: async () => {
    try {
      await api.auth.logout();
    } finally {
      set({ user: null, isAuthenticated: false });
    }
  },
}));
