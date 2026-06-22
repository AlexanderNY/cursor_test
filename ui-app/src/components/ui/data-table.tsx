import type { ReactNode } from 'react'
import { TableSkeleton } from './skeleton'
import { EmptyState } from './empty-state'

export interface DataTableColumn<T> {
  key: string
  header: string
  render?: (value: unknown, row: T) => ReactNode
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  keyExtractor: (row: T) => string | number
  isLoading?: boolean
  emptyState?: ReactNode
  emptyMessage?: string
  striped?: boolean
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyState,
  emptyMessage,
  striped = true,
}: DataTableProps<T>) {
  if (isLoading) {
    return <TableSkeleton rows={5} cols={columns.length} />
  }

  if (data.length === 0) {
    if (emptyState != null) return <>{emptyState}</>
    if (emptyMessage != null) {
      return <EmptyState title="No data" description={emptyMessage} />
    }
    return <EmptyState title="No data" />
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--border-color)]">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b border-[var(--border-color)]">
            {columns.map((col) => (
              <th
                key={col.key}
                className="text-left py-3 px-4 text-sm font-semibold text-[var(--text-primary)]"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              className={`border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors ${
                striped ? 'even:bg-[var(--bg-secondary)]/30' : ''
              }`}
            >
              {columns.map((col) => {
                const value = (row as Record<string, unknown>)[col.key]
                const content = col.render ? col.render(value, row) : (value as ReactNode)
                return (
                  <td key={col.key} className="py-3 px-4 text-[var(--text-secondary)]">
                    {content ?? '—'}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
