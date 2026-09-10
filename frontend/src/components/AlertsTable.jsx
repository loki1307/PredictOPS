/**
 * AlertsTable.jsx — Alert history table with severity badges and
 * one-click acknowledgement.
 */

import React from 'react'
import { AlertTriangle, AlertCircle, CheckCheck, Clock, Server } from 'lucide-react'
import { acknowledgeAlert } from '../api/client'

function fmtDateTime(iso) {
  try {
    const d = new Date(iso)
    return d.toLocaleString('en-IN', { hour12: false, dateStyle: 'short', timeStyle: 'medium' })
  } catch { return iso }
}

function SeverityBadge({ severity }) {
  if (severity === 'CRITICAL') return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-danger-500/20 text-danger-400 border border-danger-500/30">
      <AlertCircle size={9} />
      CRITICAL
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-warning-500/20 text-warning-400 border border-warning-500/30">
      <AlertTriangle size={9} />
      WARNING
    </span>
  )
}

export default function AlertsTable({ alerts = [], onAcknowledge, compact = false }) {

  const handleAck = async (alertId) => {
    try {
      await acknowledgeAlert(alertId)
      onAcknowledge?.()
    } catch (err) {
      console.error('Acknowledge failed:', err)
    }
  }

  if (alerts.length === 0) {
    return (
      <div className="glass-card p-8 flex flex-col items-center justify-center gap-3 text-center">
        <div className="w-12 h-12 rounded-full bg-success-500/10 border border-success-500/25 flex items-center justify-center">
          <CheckCheck size={20} className="text-success-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">All Clear</p>
          <p className="text-xs text-slate-500 mt-0.5">No alerts at this time</p>
        </div>
      </div>
    )
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-white/5">
              <th className="text-left text-slate-500 font-medium py-3 px-4">Severity</th>
              {!compact && <th className="text-left text-slate-500 font-medium py-3 px-4">Server</th>}
              <th className="text-left text-slate-500 font-medium py-3 px-4">Message</th>
              <th className="text-left text-slate-500 font-medium py-3 px-4">Prob</th>
              <th className="text-left text-slate-500 font-medium py-3 px-4">Time</th>
              <th className="text-left text-slate-500 font-medium py-3 px-4">Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert, idx) => (
              <tr
                key={alert.id}
                className={`
                  border-b border-white/5 transition-colors
                  ${alert.acknowledged ? 'opacity-40' : 'hover:bg-white/3'}
                  ${alert.severity === 'CRITICAL' && !alert.acknowledged ? 'bg-danger-500/5' : ''}
                `}
              >
                <td className="py-3 px-4">
                  <SeverityBadge severity={alert.severity} />
                </td>
                {!compact && (
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-1.5">
                      <Server size={10} className="text-slate-500" />
                      <span className="font-mono text-slate-300">{alert.server_id}</span>
                    </div>
                  </td>
                )}
                <td className="py-3 px-4 max-w-xs">
                  <p className="text-slate-300 truncate" title={alert.message}>{alert.message}</p>
                  {alert.metric && (
                    <p className="text-slate-600 mt-0.5">
                      Metric: <span className="font-mono text-slate-500">{alert.metric}</span>
                      {alert.value != null && ` = ${alert.value.toFixed(1)}`}
                    </p>
                  )}
                </td>
                <td className="py-3 px-4">
                  {alert.failure_prob != null && (
                    <span className={`font-mono font-semibold ${
                      alert.failure_prob >= 0.7 ? 'text-danger-400' :
                      alert.failure_prob >= 0.4 ? 'text-warning-400' : 'text-slate-400'
                    }`}>
                      {Math.round(alert.failure_prob * 100)}%
                    </span>
                  )}
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-1 text-slate-500">
                    <Clock size={10} />
                    <span>{fmtDateTime(alert.timestamp)}</span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  {!alert.acknowledged ? (
                    <button
                      onClick={() => handleAck(alert.id)}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded text-[10px] font-medium bg-brand-600/20 text-brand-400 border border-brand-500/30 hover:bg-brand-600/40 transition-colors"
                    >
                      <CheckCheck size={9} /> Ack
                    </button>
                  ) : (
                    <span className="text-[10px] text-slate-600 flex items-center gap-1">
                      <CheckCheck size={9} /> Acked
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
