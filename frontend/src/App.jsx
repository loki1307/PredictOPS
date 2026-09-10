/**
 * App.jsx — PredictOps root application component.
 *
 * Manages:
 *  - React Router v6 routing
 *  - Global server state (passed to Sidebar for live status dots)
 *  - API health check (passed to Sidebar)
 */

import React, { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import ServerDetail from './pages/ServerDetail'
import AlertsPage from './pages/AlertsPage'
import { fetchAlerts, fetchHealth } from './api/client'

export default function App() {
  const [servers,    setServers]    = useState([])
  const [alertCount, setAlertCount] = useState(0)
  const [apiOnline,  setApiOnline]  = useState(false)

  // ── Health check every 10s ────────────────────────────────────────────
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await fetchHealth()
        setApiOnline(true)
      } catch {
        setApiOnline(false)
      }
    }
    checkHealth()
    const id = setInterval(checkHealth, 10_000)
    return () => clearInterval(id)
  }, [])

  // ── Poll unacked alert count ──────────────────────────────────────────
  useEffect(() => {
    const pollAlerts = async () => {
      try {
        const data = await fetchAlerts({ unacknowledged_only: true, limit: 100 })
        setAlertCount(data.length)
      } catch { /* swallow */ }
    }
    pollAlerts()
    const id = setInterval(pollAlerts, 6_000)
    return () => clearInterval(id)
  }, [])

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-dark-950 bg-grid overflow-hidden">
        <Sidebar
          servers={servers}
          alertCount={alertCount}
          apiOnline={apiOnline}
        />
        <main className="flex-1 flex flex-col overflow-hidden">
          <Routes>
            <Route
              path="/"
              element={<Dashboard onServersLoad={setServers} />}
            />
            <Route path="/server/:serverId" element={<ServerDetail />} />
            <Route path="/alerts"           element={<AlertsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
