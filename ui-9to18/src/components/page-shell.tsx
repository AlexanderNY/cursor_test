import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface PageShellProps {
  children: ReactNode
  showBrandLink?: boolean
}

export function PageShell({ children, showBrandLink = true }: PageShellProps) {
  return (
    <div className="page">
      <div className="glow glow-a" aria-hidden />
      <div className="glow glow-b" aria-hidden />

      <div className="page-inner">
        {showBrandLink ? (
          <Link to="/" className="brand brand-link">
            <span className="brand-mark">9–18</span>
            <span className="brand-domain">9to18.ru</span>
          </Link>
        ) : (
          <div className="brand">
            <span className="brand-mark">9–18</span>
            <span className="brand-domain">9to18.ru</span>
          </div>
        )}

        {children}
      </div>
    </div>
  )
}
