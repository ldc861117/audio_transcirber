import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    login: (data) => client.post('/auth/login', data),
    register: (data) => client.post('/auth/register', data),
    logout: () => client.post('/auth/logout'),
    me: () => client.get('/auth/me'),
  },
  transcriptions: {
    upload: (formData) => client.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
    status: (taskId) => client.get(`/status/${taskId}`),
    list: (params = {}) => client.get('/v1/transcriptions/', { params }),
    get: (taskId) => client.get(`/v1/transcriptions/${taskId}`),
    delete: (taskId) => client.delete(`/v1/transcriptions/${taskId}`),
  },
  providers: {
    list: () => client.get('/builtin-providers'),
    test: (data) => client.post('/test-connection', data),
    testConnection: (data) => client.post('/test-connection', data),
    testConfig: () => client.get('/test-config'),
  },
  speakers: {
    list: () => client.get('/speakers'),
    rename: (id, name) => client.post(`/speakers/${id}/name`, { name }),
    delete: (id) => client.delete(`/speakers/${id}`),
    merge: (keepId, mergeId) => client.post('/speakers/merge', { keep_id: keepId, merge_id: mergeId }),
  },
  exports: {
    download: (taskId, format) => client.get(`/v1/export/${taskId}`, {
      params: { format },
      responseType: 'blob',
    }),
  },
  recordings: {
    save: (formData) => client.post('/v1/recordings/save', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
    transcribe: (taskId, config = {}) => client.post(`/v1/recordings/${taskId}/transcribe`, config),
  },
};

export default client;
