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
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    }),
    status: (taskId) => client.get(`/status/${taskId}`),
  },
  providers: {
    list: () => client.get('/builtin-providers'),
    test: (data) => client.post('/test-connection', data),
    testConfig: () => client.get('/test-config'),
  },
  speakers: {
    list: () => client.get('/speakers'),
    save: (data) => client.post('/speakers/save', data),
  }
};

export default client;
