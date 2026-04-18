import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiClient = axios.create({ baseURL: BASE_URL });

apiClient.interceptors.request.use((config) => {
  const isLoginRequest = String(config.url ?? '').includes('/auth/login');
  const token = localStorage.getItem('access_token');
  if (token && !isLoginRequest) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    const requestUrl = String(error.config?.url ?? '');
    const isLoginRequest = requestUrl.includes('/auth/login');

    console.error('API Error:', {
      url: requestUrl,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });

    if (error.response?.status === 401 && !isLoginRequest) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('enteros-role');

      if (window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
    }

    return Promise.reject(error);
  },
);

export function saveToken(token: string): void {
  localStorage.setItem('access_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('access_token');
}

export function getToken(): string | null {
  return localStorage.getItem('access_token');
}
