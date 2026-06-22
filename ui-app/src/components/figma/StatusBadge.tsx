import type { ClusterStatus } from './types'

interface StatusBadgeProps {
  status: ClusterStatus
  className?: string
}

const statusConfig: Record<ClusterStatus, { label: string; className: string }> = {
  running: {
    label: 'Running',
    className: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  },
  warning: {
    label: 'Warning',
    className: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
  },
  error: {
    label: 'Error',
    className: 'bg-red-500/20 text-red-400 border-red-500/40',
  },
  pending: {
    label: 'Pending',
    className: 'bg-slate-500/20 text-slate-400 border-slate-500/40',
  },
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const { label, className: statusClass } = statusConfig[status]
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-0.5 text-xs font-medium ${statusClass} ${className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {label}
    </span>
  )
}
