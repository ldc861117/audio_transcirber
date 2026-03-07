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
  }
}));
