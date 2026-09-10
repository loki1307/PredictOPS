/**
 * AlertsPage.jsx — Full-page alert history view with filters.
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Bell, RefreshCw } from 'lucide-react'
import AlertsTable from '../components/AlertsTable'
import { fetchAlerts } from '../api/client'

const REFRESH_INTERVAL = 8000

export default function AlertsPage() {
  const [alerts, setAlerts]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [severity, setSeverity] = useState('')
  const [unackedOnly, setUnackedOnly] = useState(false)

  const load = useCallback(async () => {
    try {
      const data = await fetchAlerts({
        limit:               100,
        severity:            severity || undefined,
        unacknowledged_only: unackedOnly,
      })
      setAlerts(data)
    } catch (err) {
      console.warn('Alerts fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [severity, unackedOnly])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [load])

  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length
  const warningCount  = alerts.filter(a => a.severity === 'WARNING').length
  const unackedCount  = alerts.filter(a => !a.acknowledged).length

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 animate-fade-in">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-danger-600/20 border border-danger-500/30 flex items-center justify-center">
            <Bell size={18} className="text-danger-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Alert Center</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              {unackedCount} unacknowledged · {criticalCount} critical · {warningCount} warnings
            </p>
          </div>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 transition-all"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* ── Stats Row ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-card p-4 border border-danger-500/20">
          <div className="text-2xl font-bold font-mono text-danger-400">{criticalCount}</div>
          <div className="text-xs text-slate-500 mt-0.5">Critical Alerts</div>
        </div>
        <div className="glass-card p-4 border border-warning-500/20">
          <div className="text-2xl font-bold font-mono text-warning-400">{warningCount}</div>
          <div className="text-xs text-slate-500 mt-0.5">Warnings</div>
        </div>
        <div className="glass-card p-4 border border-brand-500/20">
          <div className="text-2xl font-bold font-mono text-brand-400">{unackedCount}</div>
          <div className="text-xs text-slate-500 mt-0.5">Unacknowledged</div>
        </div>
      </div>

      {/* ── Filters ────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 flex-wrap">
        {['', 'CRITICAL', 'WARNING'].map(s => (
          <button
            key={s}
            onClick={() => setSeverity(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              severity === s
                ? 'bg-brand-600/30 text-brand-300 border-brand-500/40'
                : 'bg-transparent text-slate-500 border-white/10 hover:bg-white/5'
            }`}
          >
            {s === '' ? 'All Severities' : s}
          </button>
        ))}
        <div className="w-px h-5 bg-white/10" />
        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={unackedOnly}
            onChange={e => setUnackedOnly(e.target.checked)}
            className="accent-brand-500 w-3.5 h-3.5"
          />
          Unacknowledged only
        </label>
      </div>

      {/* ── Table ──────────────────────────────────────────────────────── */}
      <AlertsTable alerts={alerts} onAcknowledge={load} />
    </div>
  )
}
