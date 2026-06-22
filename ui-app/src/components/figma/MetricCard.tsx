import type { MetricCardProps as MetricType } from './types'

interface MetricCardProps extends MetricType {
  className?: string
}

const trendIcons = {
  up: (
    <svg className="h-4 w-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
    </svg>
  ),
  down: (
    <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
    </svg>
  ),
  neutral: null,
}

export function MetricCard({ label, value, subValue, trend = 'neutral', className = '' }: MetricCardProps) {
  return (
    <div
      className={`rounded-2xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-5 ${className}`}
    >
      <p className="text-sm font-medium text-[var(--text-secondary)]">{label}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-[var(--text-primary)]">{value}</span>
        {trend !== 'neutral' && trendIcons[trend]}
      </div>
      {subValue && <p className="mt-1 text-xs text-[var(--text-muted)]">{subValue}</p>}
    </div>
  )
}
