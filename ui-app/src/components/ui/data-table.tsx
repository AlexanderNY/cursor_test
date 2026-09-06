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
  /** Extra classes for each body row (e.g. ready-state highlight). */
  rowClassName?: (row: T) => string | undefined
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyState,
  emptyMessage,
  striped = true,
  rowClassName,
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
    <div className="w-full max-w-full min-w-0 overflow-x-auto overscroll-x-contain rounded-xl border border-[var(--border-color)]">
      <table className="w-full min-w-[720px] border-collapse table-auto">
        <thead>
          <tr className="border-b border-[var(--border-color)]">
            {columns.map((col) => (
              <th
                key={col.key}
                className="text-left py-2 px-2 sm:py-3 sm:px-4 text-xs sm:text-sm font-semibold text-[var(--text-primary)] whitespace-nowrap"
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const extra = rowClassName?.(row) || ''
            return (
              <tr
                key={keyExtractor(row)}
                className={`border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] transition-colors ${
                  striped && !extra ? 'even:bg-[var(--bg-secondary)]/30' : ''
                } ${extra}`}
              >
                {columns.map((col) => {
                  const value = (row as Record<string, unknown>)[col.key]
                  const content = col.render ? col.render(value, row) : (value as ReactNode)
                  return (
                    <td key={col.key} className="py-2 px-2 sm:py-3 sm:px-4 text-sm text-[var(--text-secondary)]">
                      {content ?? '—'}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
