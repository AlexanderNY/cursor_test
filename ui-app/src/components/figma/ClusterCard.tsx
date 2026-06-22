import { StatusBadge } from './StatusBadge'
import type { ClusterSummary } from './types'

interface ClusterCardProps {
  cluster: ClusterSummary
  onClick?: () => void
  className?: string
}

export function ClusterCard({ cluster, onClick, className = '' }: ClusterCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-2xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-6 text-left transition-all duration-200 hover:border-primary-500/50 hover:bg-[var(--bg-tertiary)]/50 focus:outline-none focus:ring-2 focus:ring-primary-500/50 ${className}`}
    >
      <div className="flex items-start justify-between">
        <h3 className="text-lg font-semibold text-[var(--text-primary)]">{cluster.name}</h3>
        <StatusBadge status={cluster.status} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-[var(--text-muted)]">Nodes</p>
          <p className="font-medium text-[var(--text-primary)]">{cluster.nodeCount}</p>
        </div>
        <div>
          <p className="text-[var(--text-muted)]">Pods</p>
          <p className="font-medium text-[var(--text-primary)]">{cluster.podCount}</p>
        </div>
        <div>
          <p className="text-[var(--text-muted)]">CPU</p>
          <p className="font-medium text-[var(--text-primary)]">{cluster.cpuUsage}%</p>
        </div>
        <div>
          <p className="text-[var(--text-muted)]">Memory</p>
          <p className="font-medium text-[var(--text-primary)]">{cluster.memoryUsage}%</p>
        </div>
      </div>
    </button>
  )
}
