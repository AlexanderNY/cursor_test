import type { ReactNode } from 'react'

const PAGE_MAX_WIDTH_DEFAULT = 'max-w-4xl'
const PAGE_MAX_WIDTH_WIDE = 'max-w-6xl'

interface PageContainerProps {
  children: ReactNode
  maxWidth?: 'default' | 'wide'
  className?: string
}

export function PageContainer({
  children,
  maxWidth = 'default',
  className = '',
}: PageContainerProps) {
  const maxWidthClass = maxWidth === 'wide' ? PAGE_MAX_WIDTH_WIDE : PAGE_MAX_WIDTH_DEFAULT
  return (
    <div
      className={`mx-auto space-y-6 animate-fade-in ${maxWidthClass} ${className}`.trim()}
    >
      {children}
    </div>
  )
}

export { PAGE_MAX_WIDTH_DEFAULT, PAGE_MAX_WIDTH_WIDE }
