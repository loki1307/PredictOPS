/**
 * client.js — Axios API client for PredictOps dashboard.
 * All API calls go through these helpers so the base URL is configured once.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 8000,
})

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
