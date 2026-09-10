/**
 * Dashboard.jsx — Main dashboard page.
 *
 * Displays:
 *  - Top stats bar: total servers, warning, critical counts, uptime
 *  - Server grid with ServerCard components
 *  - Recent alert panel
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Activity, Server, AlertTriangle, AlertCircle, Clock, RefreshCw } from 'lucide-react'
import ServerCard from '../components/ServerCard'
import AlertsTable from '../components/AlertsTable'
import { fetchServersSummary, fetchAlerts } from '../api/client'

const REFRESH_INTERVAL = 5000   // ms

function StatCard({ icon: Icon, label, value, color, pulse }) {
  return (
    <div className="glass-card px-5 py-4 flex items-center gap-4">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
        <Icon size={18} className="text-white" />
      </div>
      <div>
        <div className={`text-2xl font-bold font-mono text-white ${pulse ? 'animate-pulse-slow' : ''}`}>{value}</div>
        <div className="text-xs text-slate-500 mt-0.5">{label}</div>
      </div>
    </div>
  )
}

export default function Dashboard({ onServersLoad }) {
  const [servers, setServers]   = useState([])
  const [alerts,  setAlerts]    = useState([])
  const [loading, setLoading]   = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [filter, setFilter]     = useState('all')   // all | healthy | warning | critical

  const load = useCallback(async () => {
    try {
      const [srvData, alertData] = await Promise.all([
        fetchServersSummary(),
        fetchAlerts({ limit: 20 }),
      ])
      setServers(srvData)
      setAlerts(alertData)
      onServersLoad?.(srvData)
      setLastRefresh(new Date())
    } catch (err) {
      console.warn('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [onServersLoad])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [load])

  // ── Stats ──────────────────────────────────────────────────────────────
  const total    = servers.length
  const criticals = servers.filter(s => s.status === 'critical').length
  const warnings  = servers.filter(s => s.status === 'warning').length
  const healthy   = servers.filter(s => s.status === 'healthy').length

  const uptimePct = total > 0
    ? Math.round(((total - criticals) / total) * 100)
    : 100

  // ── Filter ─────────────────────────────────────────────────────────────
  const filteredServers = servers.filter(s =>
    filter === 'all' ? true : s.status === filter
  )

  const unackedCount = alerts.filter(a => !a.acknowledged).length

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 animate-fade-in">

      {/* ── Page Header ────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Infrastructure Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time predictive monitoring · Auto-refresh every 5s
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 transition-all"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString('en-IN', { hour12: false })}` : 'Refresh'}
        </button>
      </div>

      {/* ── Stats Bar ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Server}        label="Total Servers"  value={total}      color="bg-brand-600"   />
        <StatCard icon={Activity}      label="Uptime"         value={`${uptimePct}%`} color="bg-success-600"  />
        <StatCard icon={AlertTriangle} label="Warnings"       value={warnings}   color="bg-warning-600" pulse={warnings > 0} />
        <StatCard icon={AlertCircle}   label="Critical"       value={criticals}  color="bg-danger-600"  pulse={criticals > 0} />
      </div>

      {/* ── Filter Tabs ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2">
        {['all', 'healthy', 'warning', 'critical'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all border ${
              filter === f
                ? 'bg-brand-600/30 text-brand-300 border-brand-500/40'
                : 'bg-transparent text-slate-500 border-white/10 hover:bg-white/5 hover:text-slate-300'
            }`}
          >
            {f} {f !== 'all' && `(${servers.filter(s => s.status === f).length})`}
          </button>
        ))}
      </div>

      {/* ── Server Grid ────────────────────────────────────────────────── */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="glass-card h-52 animate-pulse bg-white/3" />
          ))}
        </div>
      ) : filteredServers.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredServers.map(srv => (
            <ServerCard key={srv.server_id} server={srv} />
          ))}
        </div>
      ) : (
        <div className="glass-card p-12 text-center">
          <p className="text-slate-500 text-sm">
            {servers.length === 0
              ? 'No server data yet — start the simulator to begin'
              : `No servers with status "${filter}"`}
          </p>
        </div>
      )}

      {/* ── Recent Alerts ──────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-white">
            Recent Alerts
            {unackedCount > 0 && (
              <span className="ml-2 px-1.5 py-0.5 text-[10px] font-bold bg-danger-500 text-white rounded-full">
                {unackedCount} new
              </span>
            )}
          </h2>
        </div>
        <AlertsTable alerts={alerts} onAcknowledge={load} />
      </div>
    </div>
  )
}
