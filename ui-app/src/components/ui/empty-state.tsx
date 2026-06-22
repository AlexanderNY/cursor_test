import type { ReactNode } from 'react'
import { DocumentTextIcon } from '@/components/icons'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div className={`text-center py-8 ${className}`.trim()}>
      <div className="flex justify-center text-[var(--text-muted)] mb-3">
        {icon ?? <DocumentTextIcon className="h-12 w-12" />}
      </div>
      <h3 className="text-lg font-medium text-[var(--text-primary)]">{title}</h3>
      {description != null && (
        <p className="mt-1 text-sm text-[var(--text-secondary)] max-w-sm mx-auto">{description}</p>
      )}
      {action != null && <div className="mt-4">{action}</div>}
    </div>
  )
}
