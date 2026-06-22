import { StatusBadge } from './StatusBadge'
import type { NodeRow } from './types'

interface NodeTableProps {
  nodes: NodeRow[]
  className?: string
}

const headers = ['Name', 'Status', 'Roles', 'CPU', 'Memory', 'Age'] as const

export function NodeTable({ nodes, className = '' }: NodeTableProps) {
  return (
    <div className={`overflow-hidden rounded-2xl border border-[var(--border-color)] bg-[var(--bg-secondary)] ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-[var(--border-color)] bg-[var(--bg-tertiary)]/50">
              {headers.map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left font-semibold text-[var(--text-secondary)]"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {nodes.map((node, i) => (
              <tr
                key={node.name}
                className={`border-b border-[var(--border-color)]/60 transition-colors hover:bg-[var(--bg-tertiary)]/30 ${
                  i === nodes.length - 1 ? 'border-b-0' : ''
                }`}
              >
                <td className="px-4 py-3 font-medium text-[var(--text-primary)]">{node.name}</td>
                <td className="px-4 py-3">
                  <StatusBadge status={node.status} />
                </td>
                <td className="px-4 py-3 text-[var(--text-secondary)]">{node.roles.join(', ')}</td>
                <td className="px-4 py-3 text-[var(--text-primary)]">{node.cpu}</td>
                <td className="px-4 py-3 text-[var(--text-primary)]">{node.memory}</td>
                <td className="px-4 py-3 text-[var(--text-muted)]">{node.age}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
