/**
 * FailureGauge.jsx — Radial gauge showing failure probability for a server.
 * Uses Recharts RadialBarChart.
 */

import React from 'react'
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { TrendingUp, ShieldAlert, Shield, ShieldCheck } from 'lucide-react'

function getRiskConfig(prob) {
  if (prob >= 0.70) return {
    label: 'CRITICAL',
    color: '#ef4444',
    bg:    'bg-danger-500/10',
    border:'border-danger-500/30',
    text:  'text-danger-400',
    icon:  ShieldAlert,
    glow:  'shadow-glow-red',
    desc:  'Failure imminent. Immediate action required.',
  }
  if (prob >= 0.45) return {
    label: 'HIGH RISK',
    color: '#f59e0b',
    bg:    'bg-warning-500/10',
    border:'border-warning-500/30',
    text:  'text-warning-400',
    icon:  ShieldAlert,
    glow:  'shadow-glow-amber',
    desc:  'Degradation detected. Monitor closely.',
  }
  if (prob >= 0.20) return {
    label: 'MEDIUM',
    color: '#3b72f8',
    bg:    'bg-brand-500/10',
    border:'border-brand-500/25',
    text:  'text-brand-400',
    icon:  Shield,
    glow:  'shadow-glow-blue',
    desc:  'Minor anomalies observed.',
  }
  return {
    label: 'LOW RISK',
    color: '#22c55e',
    bg:    'bg-success-500/10',
    border:'border-success-500/25',
    text:  'text-success-400',
    icon:  ShieldCheck,
    glow:  'shadow-glow-green',
    desc:  'Server operating normally.',
  }
}

export default function FailureGauge({ failureProb = 0, anomalyScore = 0 }) {
  const prob   = Math.max(0, Math.min(1, failureProb))
  const pct    = Math.round(prob * 100)
  const cfg    = getRiskConfig(prob)
  const Icon   = cfg.icon

  const chartData = [{ name: 'risk', value: pct, fill: cfg.color }]

  return (
    <div className={`glass-card p-5 border ${cfg.border}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-white">Failure Probability</h3>
          <p className="text-xs text-slate-500 mt-0.5">Next 15 minutes</p>
        </div>
        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${cfg.bg} ${cfg.text} border ${cfg.border}`}>
          <Icon size={11} />
          {cfg.label}
        </div>
      </div>

      {/* ── Radial Gauge ───────────────────────────────────────────────── */}
      <div className="relative h-52">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="60%"
            innerRadius="70%"
            outerRadius="90%"
            startAngle={180}
            endAngle={0}
            data={chartData}
            barSize={16}
          >
            {/* Background track */}
            <RadialBar
              background={{ fill: 'rgba(255,255,255,0.04)' }}
              dataKey="value"
              cornerRadius={8}
              data={[{ name: 'bg', value: 100, fill: 'rgba(255,255,255,0.04)' }]}
            />
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              dataKey="value"
              cornerRadius={8}
              data={chartData}
              isAnimationActive
              animationDuration={800}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        {/* ── Center Text ─────────────────────────────────────────────── */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pb-8">
          <div className={`text-4xl font-bold font-mono ${cfg.text}`}>{pct}%</div>
          <div className="text-xs text-slate-500 mt-1">probability</div>
        </div>
      </div>

      {/* ── Description ───────────────────────────────────────────────── */}
      <p className={`text-xs ${cfg.text} text-center mt-2`}>{cfg.desc}</p>

      {/* ── Anomaly Score ─────────────────────────────────────────────── */}
      <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <TrendingUp size={12} className="text-slate-500" />
          <span className="text-xs text-slate-500">Anomaly Score</span>
        </div>
        <span className={`text-xs font-mono font-semibold ${
          anomalyScore < -0.1 ? 'text-danger-400' : 'text-success-400'
        }`}>
          {anomalyScore?.toFixed(4) ?? 'N/A'}
          {anomalyScore < -0.1 && (
            <span className="ml-1.5 text-[10px] px-1.5 py-0.5 bg-danger-500/20 rounded-full">anomalous</span>
          )}
        </span>
      </div>
    </div>
  )
}
