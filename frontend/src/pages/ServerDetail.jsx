/**
 * ServerDetail.jsx — Per-server deep-dive page.
 *
 * Displays:
 *  - Server header with current status
 *  - Failure probability gauge (FailureGauge)
 *  - Live metrics chart (MetricsChart)
 *  - Server-specific alert history (AlertsTable)
 */

import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, RefreshCw, Cpu, MemoryStick, HardDrive, Wifi, Activity } from 'lucide-react'
import MetricsChart from '../components/MetricsChart'
import FailureGauge from '../components/FailureGauge'
import AlertsTable from '../components/AlertsTable'
import { fetchMetrics, fetchAlerts } from '../api/client'

const REFRESH_INTERVAL = 5000

const SERVER_ICONS = {
  'web-01': '🌐', 'db-01': '🗄️', 'cache-01': '⚡',
  'app-01': '📦', 'queue-01': '🔄', 'lb-01': '⚖️',
}

function MetricTile({ icon: Icon, label, value, unit, max = 100, color }) {
  const pct = Math.min(100, (value / max) * 100)
  const barColor = pct > 80 ? '#ef4444' : pct > 60 ? '#f59e0b' : '#22c55e'
  return (
    <div className="glass-card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-brand-600/20 flex items-center justify-center">
            <Icon size={13} className="text-brand-400" />
          </div>
          <span className="text-xs text-slate-400 font-medium">{label}</span>
        </div>
        <span className="metric-value text-xl" style={{ color }}>
          {typeof value === 'number' ? value.toFixed(1) : '—'}
          <span className="text-xs text-slate-500 font-normal ml-0.5">{unit}</span>
        </span>
      </div>
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${pct}%`, background: barColor }}
        />
      </div>
    </div>
  )
}

export default function ServerDetail() {
  const { serverId } = useParams()
  const [metrics, setMetrics]   = useState([])
  const [alerts,  setAlerts]    = useState([])
  const [loading, setLoading]   = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)

  const latest = metrics[metrics.length - 1] || null

  const load = useCallback(async () => {
    try {
      const [mData, aData] = await Promise.all([
        fetchMetrics(serverId, 80),
        fetchAlerts({ server_id: serverId, limit: 30 }),
      ])
      setMetrics(mData)
      setAlerts(aData)
      setLastRefresh(new Date())
    } catch (err) {
      console.warn('ServerDetail fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [serverId])

  useEffect(() => {
    setMetrics([])
    setAlerts([])
    setLoading(true)
    load()
    const id = setInterval(load, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [load])

  const status = latest?.status || 'healthy'
  const statusConfig = {
    healthy:  { text: 'text-success-400', dot: 'bg-success-400', label: 'Healthy'  },
    warning:  { text: 'text-warning-400', dot: 'bg-warning-400', label: 'Warning'  },
    critical: { text: 'text-danger-400',  dot: 'bg-danger-400',  label: 'Critical' },
  }[status] || { text: 'text-slate-400', dot: 'bg-slate-400', label: 'Unknown' }

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6 animate-fade-in">

      {/* ── Breadcrumb / Header ────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <ArrowLeft size={13} /> Dashboard
          </Link>
          <div className="w-px h-4 bg-white/10" />
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-dark-800 border border-white/10 flex items-center justify-center text-2xl">
              {SERVER_ICONS[serverId] || '🖥️'}
            </div>
            <div>
              <h1 className="text-xl font-bold text-white font-mono">{serverId}</h1>
              <div className={`flex items-center gap-1.5 text-xs ${statusConfig.text} mt-0.5`}>
                <span className={`w-1.5 h-1.5 rounded-full ${statusConfig.dot} animate-pulse`} />
                {statusConfig.label}
              </div>
            </div>
          </div>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 transition-all"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          {lastRefresh ? lastRefresh.toLocaleTimeString('en-IN', { hour12: false }) : 'Refresh'}
        </button>
      </div>

      {/* ── Current Metric Tiles ─────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricTile icon={Cpu}        label="CPU"       value={latest?.cpu_percent}     unit="%" color="#3b72f8" />
        <MetricTile icon={MemoryStick}label="Memory"    value={latest?.memory_percent}  unit="%" color="#8b5cf6" />
        <MetricTile icon={HardDrive}  label="Disk I/O"  value={latest?.disk_io_percent} unit="%" color="#f59e0b" />
        <MetricTile icon={Wifi}       label="Latency"   value={latest?.net_latency_ms}  unit="ms" max={500} color="#22c55e" />
      </div>

      {/* ── Chart + Gauge ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <MetricsChart data={metrics} />
        </div>
        <div>
          <FailureGauge
            failureProb={latest?.failure_prob ?? 0}
            anomalyScore={latest?.anomaly_score ?? 0}
          />
        </div>
      </div>

      {/* ── Packet Loss Sparkline ─────────────────────────────────────── */}
      <div className="glass-card p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-danger-400" />
          <span className="text-sm text-slate-300 font-medium">Packet Loss</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xl font-bold text-danger-400">
            {latest?.packet_loss_pct?.toFixed(2) ?? '—'}
            <span className="text-xs text-slate-500 font-normal ml-0.5">%</span>
          </span>
          <div className="progress-bar-track w-32">
            <div
              className="progress-bar-fill bg-danger-500"
              style={{ width: `${Math.min(100, (latest?.packet_loss_pct ?? 0) * 2)}%` }}
            />
          </div>
        </div>
      </div>

      {/* ── Alert History ─────────────────────────────────────────────── */}
      <div>
        <h2 className="text-base font-semibold text-white mb-3">
          Alert History
          <span className="ml-2 text-xs text-slate-500 font-normal">for {serverId}</span>
        </h2>
        <AlertsTable alerts={alerts} onAcknowledge={load} compact />
      </div>
    </div>
  )
}
