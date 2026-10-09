/**
 * client.js — Axios API client for PredictOps dashboard.
 * All API calls go through these helpers so the base URL is configured once.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 8000,
})

// Add a request interceptor to include the auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and maybe reload or redirect
      localStorage.removeItem('token');
      // If we are not already on the login page, redirect
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────
export const loginUser = (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  return api.post('/auth/login', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    }
  }).then(r => r.data);
};

export const setupFirstUser = (username, email, password) => {
  return api.post('/auth/setup', { username, email, password }).then(r => r.data);
};

// ── Servers ───────────────────────────────────────────────────────────────
export const fetchServersSummary = () =>
  api.get('/servers/summary').then(r => r.data)

// ── Metrics ───────────────────────────────────────────────────────────────
export const fetchMetrics = (serverId, limit = 60) =>
  api.get(`/metrics/${serverId}`, { params: { limit } }).then(r => r.data)

// ── Predictions ───────────────────────────────────────────────────────────
export const fetchPrediction = (serverId) =>
  api.get(`/predictions/${serverId}`).then(r => r.data)

// ── Alerts ───────────────────────────────────────────────────────────────
export const fetchAlerts = (params = {}) =>
  api.get('/alerts', { params }).then(r => r.data)

export const acknowledgeAlert = (alertId) =>
  api.post(`/alerts/${alertId}/acknowledge`, { acknowledged: true }).then(r => r.data)

export const fetchAlertStats = () =>
  api.get('/alerts/stats/summary').then(r => r.data)

// ── Health ────────────────────────────────────────────────────────────────
export const fetchHealth = () =>
  api.get('/health').then(r => r.data)
