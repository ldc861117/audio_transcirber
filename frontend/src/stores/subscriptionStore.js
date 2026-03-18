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
    try {
      const res = await api.subscriptions.plans();
      const raw = res.data.data;
      // Backend returns { free: {...}, basic: {...}, pro: {...} }
      // Frontend expects an array with an `id` field on each plan
      const planOrder = ["free", "basic", "pro"];
      const plans = planOrder
        .filter((key) => raw[key])
        .map((key) => ({ id: key, ...raw[key] }));
      set({ plans });
    } catch {
      set({ plans: [] });
    }
  },

  fetchUsage: async () => {
    try {
      const res = await api.subscriptions.usage();
      const raw = res.data.data;
      // Backend returns { total_used, quota, remaining, tier, history }
      // Frontend expects { minutes_used, monthly_minutes_limit }
      set({
        usage: {
          minutes_used: raw.total_used ?? 0,
          monthly_minutes_limit: raw.quota ?? 60,
          remaining: raw.remaining ?? 0,
          tier: raw.tier ?? "free",
          history: raw.history ?? [],
        },
      });
    } catch {
      // Provide sensible defaults to avoid NaN
      set({
        usage: {
          minutes_used: 0,
          monthly_minutes_limit: 60,
          remaining: 60,
          tier: "free",
          history: [],
        },
      });
    }
  },

  fetchInvoices: async () => {
    try {
      const res = await api.subscriptions.invoices();
      // invoices endpoint returns { data: [...] } directly (not nested)
      const data = res.data.data;
      set({ invoices: Array.isArray(data) ? data : [] });
    } catch {
      set({ invoices: [] });
    }
  },

  checkout: async (tier, cycle) => {
    const res = await api.subscriptions.checkout({
      tier,
      cycle,
      success_url: `${window.location.origin}/account?checkout=success`,
      cancel_url: `${window.location.origin}/pricing?checkout=cancelled`,
    });
    // Redirect to Stripe Checkout
    if (res.data.data.checkout_url) {
      window.location.href = res.data.data.checkout_url;
    }
  },

  cancelSubscription: async () => {
    await api.subscriptions.cancel();
    const res = await api.subscriptions.me();
    set({ subscription: res.data.data });
  },

  reactivateSubscription: async () => {
    await api.subscriptions.reactivate();
    const res = await api.subscriptions.me();
    set({ subscription: res.data.data });
  },
}));
