/**
 * MetricsChart.jsx — Multi-line Recharts chart for server metrics.
 * Shows the last N data points for CPU, Memory, Disk I/O, and Net Latency.
 */

import React, { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'

// Inline time formatter (avoids adding date-fns dependency)
function fmtTime(iso) {
  try {
    const d = new Date(iso)
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`
  } catch { return '' }
}

const METRIC_LINES = [
  { key: 'cpu_percent',     name: 'CPU %',     color: '#3b72f8', yAxis: 'percent' },
  { key: 'memory_percent',  name: 'Memory %',  color: '#8b5cf6', yAxis: 'percent' },
  { key: 'disk_io_percent', name: 'Disk I/O %',color: '#f59e0b', yAxis: 'percent' },
  { key: 'net_latency_ms',  name: 'Latency ms',color: '#22c55e', yAxis: 'latency' },
  { key: 'packet_loss_pct', name: 'Pkt Loss %',color: '#ef4444', yAxis: 'packet'  },
]

// Custom tooltip
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 text-xs min-w-[180px]">
      <p className="text-slate-400 mb-2 font-mono">{label}</p>
      {payload.map(p => (
        <div key={p.dataKey} className="flex items-center justify-between gap-4 mb-1">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-slate-300">{p.name}</span>
          </div>
          <span className="font-mono font-semibold" style={{ color: p.color }}>
            {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function MetricsChart({ data = [] }) {
  const [hidden, setHidden] = useState({})

  const chartData = data.map(d => ({
    ...d,
    _time: fmtTime(d.timestamp),
  }))

  const toggleLine = (key) => setHidden(h => ({ ...h, [key]: !h[key] }))

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">Live Metrics</h3>
        <span className="text-xs text-slate-500">{data.length} samples</span>
      </div>

      {/* ── Legend toggles ───────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-2 mb-4">
        {METRIC_LINES.map(({ key, name, color }) => (
          <button
            key={key}
            onClick={() => toggleLine(key)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
              hidden[key]
                ? 'border-white/10 text-slate-600 bg-transparent'
                : 'border-white/20 text-slate-300 bg-white/5'
            }`}
          >
            <div
              className="w-2 h-2 rounded-full transition-opacity"
              style={{ background: color, opacity: hidden[key] ? 0.2 : 1 }}
            />
            {name}
          </button>
        ))}
      </div>

      {data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-slate-600 text-sm">
          Waiting for metrics data…
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis
              dataKey="_time"
              tick={{ fontSize: 10, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              yAxisId="percent"
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => `${v}%`}
            />
            <YAxis
              yAxisId="latency"
              orientation="right"
              domain={[0, 500]}
              tick={{ fontSize: 10, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={v => `${v}ms`}
            />
            <YAxis
              yAxisId="packet"
              hide
              domain={[0, 50]}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              yAxisId="percent"
              y={80}
              stroke="rgba(239,68,68,0.3)"
              strokeDasharray="4 4"
              label={{ value: 'Critical', fontSize: 9, fill: '#ef4444', position: 'right' }}
            />
            {METRIC_LINES.map(({ key, name, color, yAxis }) => (
              <Line
                key={key}
                yAxisId={yAxis}
                type="monotone"
                dataKey={key}
                name={name}
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
                hide={hidden[key]}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
