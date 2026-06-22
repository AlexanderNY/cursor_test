import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">{title}</h1>
        {description != null && (
          <p className="text-[var(--text-secondary)] mt-1">{description}</p>
        )}
      </div>
      {actions != null && (
        <div className="flex items-center shrink-0 mt-2 sm:mt-0">{actions}</div>
      )}
    </div>
  )
}
