/**
 * ServerCard.jsx — Grid card representing one server's current state.
 * Shows status badge, key metrics, failure probability bar, and a
 * link to the detailed server view.
 */

import React from 'react'
import { Link } from 'react-router-dom'
import { Cpu, MemoryStick, Wifi, ArrowRight, TrendingUp } from 'lucide-react'

const SERVER_ICONS = {
  'web-01':   '🌐',
  'db-01':    '🗄️',
  'cache-01': '⚡',
  'app-01':   '📦',
  'queue-01': '🔄',
  'lb-01':    '⚖️',
}

const STATUS_CONFIG = {
  healthy: {
    label:   'Healthy',
    bg:      'bg-success-500/10',
    border:  'border-success-500/25',
    text:    'text-success-400',
    bar:     'bg-success-500',
    glow:    'shadow-glow-green',
    dot:     'bg-success-400',
  },
  warning: {
    label:   'Warning',
    bg:      'bg-warning-500/10',
    border:  'border-warning-500/25',
    text:    'text-warning-400',
    bar:     'bg-warning-500',
    glow:    'shadow-glow-amber',
    dot:     'bg-warning-400',
  },
  critical: {
    label:   'Critical',
    bg:      'bg-danger-500/10',
    border:  'border-danger-500/30',
    text:    'text-danger-400',
    bar:     'bg-danger-500',
    glow:    'shadow-glow-red',
    dot:     'bg-danger-400',
  },
}

function MiniBar({ value, max = 100, colorClass }) {
  const pct = Math.min(100, (value / max) * 100)
  const barColor =
    pct > 80 ? 'bg-danger-500' :
    pct > 60 ? 'bg-warning-500' :
               'bg-success-500'
  return (
    <div className="progress-bar-track flex-1">
      <div
        className={`progress-bar-fill ${barColor}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

export default function ServerCard({ server }) {
  const status   = server.status || 'healthy'
  const cfg      = STATUS_CONFIG[status] || STATUS_CONFIG.healthy
  const prob     = Math.round((server.failure_prob || 0) * 100)
  const icon     = SERVER_ICONS[server.server_id] || '🖥️'

  return (
    <Link
      to={`/server/${server.server_id}`}
      className={`
        glass-card p-5 block group hover:border-brand-500/40 hover:scale-[1.02]
        transition-all duration-300 cursor-pointer
        border ${cfg.border}
        animate-fade-in
      `}
    >
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`
            w-10 h-10 rounded-xl flex items-center justify-center text-xl
            ${cfg.bg} border ${cfg.border}
          `}>
            {icon}
          </div>
          <div>
            <div className="font-mono font-semibold text-white text-sm">{server.server_id}</div>
            <div className={`text-xs font-medium ${cfg.text} flex items-center gap-1.5 mt-0.5`}>
              <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} animate-pulse`} />
              {cfg.label}
            </div>
          </div>
        </div>
        <ArrowRight
          size={16}
          className="text-slate-600 group-hover:text-brand-400 group-hover:translate-x-1 transition-all"
        />
      </div>

      {/* ── Metrics ────────────────────────────────────────────────────── */}
      <div className="space-y-2.5 mb-4">
        <div className="flex items-center gap-2">
          <Cpu size={12} className="text-slate-500 shrink-0" />
          <span className="text-xs text-slate-500 w-14">CPU</span>
          <MiniBar value={server.cpu_percent} />
          <span className="text-xs font-mono text-slate-300 w-10 text-right">
            {server.cpu_percent?.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <MemoryStick size={12} className="text-slate-500 shrink-0" />
          <span className="text-xs text-slate-500 w-14">Memory</span>
          <MiniBar value={server.memory_percent} />
          <span className="text-xs font-mono text-slate-300 w-10 text-right">
            {server.memory_percent?.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Wifi size={12} className="text-slate-500 shrink-0" />
          <span className="text-xs text-slate-500 w-14">Latency</span>
          <MiniBar value={server.net_latency_ms} max={500} />
          <span className="text-xs font-mono text-slate-300 w-10 text-right">
            {server.net_latency_ms?.toFixed(0)}ms
          </span>
        </div>
      </div>

      {/* ── Failure Probability ─────────────────────────────────────────── */}
      <div className={`rounded-lg p-3 ${cfg.bg} border ${cfg.border}`}>
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-1.5">
            <TrendingUp size={11} className={cfg.text} />
            <span className="text-[11px] text-slate-400 font-medium">Failure Risk (15 min)</span>
          </div>
          <span className={`text-sm font-bold font-mono ${cfg.text}`}>{prob}%</span>
        </div>
        <div className="progress-bar-track">
          <div
            className={`progress-bar-fill ${cfg.bar}`}
            style={{ width: `${prob}%` }}
          />
        </div>
      </div>
    </Link>
  )
}
