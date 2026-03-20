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
  recordings: {
    start: () => client.post("/recordings/start"),
    appendChunk: (sessionId, formData) =>
      client.post(`/recordings/${sessionId}/chunk`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      }),
    finalize: (sessionId, options = {}) =>
      client.post(`/recordings/${sessionId}/finalize`, options),
  },
};
