import client, { cloudClient } from "./client";

export const api = {
  // ── Auth & Subscriptions → Cloud Run ──
  auth: {
    register: (data) => cloudClient.post("/auth/register", data),
    login: (data) => cloudClient.post("/auth/login", data),
    refresh: (data) => cloudClient.post("/auth/refresh", data),
    logout: () => cloudClient.post("/auth/logout"),
    me: () => cloudClient.get("/auth/me"),
    updateProfile: (data) => cloudClient.put("/auth/me", data),
    changePassword: (data) => cloudClient.post("/auth/change-password", data),
  },
  subscriptions: {
    plans: () => cloudClient.get("/subscriptions/plans"),
    me: () => cloudClient.get("/subscriptions/me"),
    checkout: (data) => cloudClient.post("/subscriptions/checkout", data),
    cancel: () => cloudClient.post("/subscriptions/cancel"),
    reactivate: () => cloudClient.post("/subscriptions/reactivate"),
    usage: () => cloudClient.get("/subscriptions/usage"),
    invoices: () => cloudClient.get("/subscriptions/invoices"),
    portal: (data) => cloudClient.post("/subscriptions/portal", data),
  },

  // ── Transcription & Data → Local Flask ──
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
    updateTaskSpeakers: (taskId, speakers, saveToLibrary = false) =>
      client.post(`/speakers/task/${taskId}/update`, {
        speakers,
        save_to_library: saveToLibrary,
      }),
  },
  exports: {
    download: (taskId, format) =>
      client.get(`/export/${taskId}`, {
        params: { format },
        responseType: "blob",
      }),
  },
  // Alias for Settings page compatibility
  providers: {
    list: () => client.get("/transcriptions/providers"),
    testConnection: (data) =>
      client.post("/transcriptions/test-connection", data),
  },
};
