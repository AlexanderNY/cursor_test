import type { ReactNode } from 'react'

const PAGE_MAX_WIDTH = {
  default: 'max-w-5xl',
  wide: 'max-w-none',
  full: 'max-w-none',
} as const

interface PageContainerProps {
  children: ReactNode
  maxWidth?: keyof typeof PAGE_MAX_WIDTH
  className?: string
}

export function PageContainer({
  children,
  maxWidth = 'full',
  className = '',
}: PageContainerProps) {
  const maxWidthClass = PAGE_MAX_WIDTH[maxWidth]
  return (
    <div
      className={`mx-auto w-full min-w-0 space-y-4 sm:space-y-6 animate-fade-in ${maxWidthClass} ${className}`.trim()}
    >
      {children}
    </div>
  )
}

export { PAGE_MAX_WIDTH }
