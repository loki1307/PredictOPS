/**
 * Sidebar.jsx — Left navigation sidebar for PredictOps dashboard.
 */

import React from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import {
  Activity, Server, Bell, BarChart3, Zap, Shield,
  AlertTriangle, CheckCircle, XCircle, LogOut
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/',        icon: BarChart3,     label: 'Dashboard'   },
  { to: '/alerts',  icon: Bell,          label: 'Alerts'      },
]



const SERVER_ICONS = {
  'web-01':   '🌐',
  'db-01':    '🗄️',
  'cache-01': '⚡',
  'app-01':   '📦',
  'queue-01': '🔄',
  'lb-01':    '⚖️',
}

function StatusDot({ status }) {
  const cls = {
    healthy:  'status-dot healthy',
    warning:  'status-dot warning',
    critical: 'status-dot critical',
  }[status] || 'status-dot healthy'
  return <span className={cls} />
}

export default function Sidebar({ servers = [], alertCount = 0, apiOnline = true }) {
  const location = useLocation()
  const navigate = useNavigate()

  return (
    <aside className="flex flex-col w-64 min-h-screen bg-dark-900 border-r border-white/5 shrink-0">
      {/* ── Logo ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/5">
        <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-violet-500 shadow-glow-blue">
          <Zap size={18} className="text-white" fill="white" />
        </div>
        <div>
          <div className="text-base font-bold text-white tracking-tight">PredictOps</div>
          <div className="text-[10px] text-brand-400 font-medium uppercase tracking-widest">AIOps Platform</div>
        </div>
      </div>

      {/* ── API Status ───────────────────────────────────────────────────── */}
      <div className="mx-4 mt-4 px-3 py-2 rounded-lg bg-dark-800 border border-white/5 flex items-center gap-2">
        {apiOnline ? (
          <>
            <CheckCircle size={12} className="text-success-400 shrink-0" />
            <span className="text-xs text-success-400 font-medium">API Connected</span>
          </>
        ) : (
          <>
            <XCircle size={12} className="text-danger-400 shrink-0" />
            <span className="text-xs text-danger-400 font-medium">API Offline</span>
          </>
        )}
      </div>

      {/* ── Main Nav ─────────────────────────────────────────────────────── */}
      <nav className="px-3 mt-6">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 px-3 mb-2">Navigation</p>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `sidebar-link flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm font-medium transition-all ` +
              (isActive
                ? 'active bg-brand-600/20 text-brand-300'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200')
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? 'text-brand-400' : ''} />
                <span>{label}</span>
                {label === 'Alerts' && alertCount > 0 && (
                  <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold bg-danger-500 text-white rounded-full">
                    {alertCount > 99 ? '99+' : alertCount}
                  </span>
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* ── Server List ──────────────────────────────────────────────────── */}
      <nav className="px-3 mt-6">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 px-3 mb-2">Servers</p>
        {servers.length === 0 && (
          <p className="text-xs text-slate-500 px-3 py-1 italic">No servers active</p>
        )}
        {servers.map((srv) => {
          const sid = srv.server_id
          const icon = SERVER_ICONS[sid] || '🖥️'
          return (
            <NavLink
              key={sid}
              to={`/server/${sid}`}
              className={({ isActive }) =>
                `sidebar-link flex items-center gap-3 px-3 py-2 rounded-lg mb-1 text-sm transition-all ` +
                (isActive
                  ? 'active bg-brand-600/20 text-white'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-200')
              }
            >
              <span className="text-base w-5 text-center">{icon}</span>
              <span className="flex-1 font-mono text-xs truncate" title={sid}>{sid}</span>
              <StatusDot status={srv.status} />
            </NavLink>
          )
        })}
      </nav>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <div className="mt-auto px-4 py-4 border-t border-white/5">
        <div className="flex items-center gap-2 px-3 text-xs text-slate-600">
          <Shield size={12} />
          <span>PredictOps v1.0 · Real-Time Monitoring</span>
        </div>
      </div>
    </aside>
  )
}
