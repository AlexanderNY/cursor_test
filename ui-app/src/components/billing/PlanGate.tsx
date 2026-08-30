import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'

type Props = {
  allowed: boolean
  featureLabel: string
  children: ReactNode
  /** Compact banner instead of replacing children */
  soft?: boolean
  className?: string
}

export function PlanGate({ allowed, featureLabel, children, soft = false, className = '' }: Props) {
  if (allowed) return <>{children}</>

  const banner = (
    <Alert variant="info" className={className}>
      <span>
        {featureLabel} requires a higher plan.{' '}
        <Link to="/pricing" className="underline text-primary-400 hover:text-primary-300">
          View pricing
        </Link>
      </span>
    </Alert>
  )

  if (soft) {
    return (
      <div className="space-y-3">
        {banner}
        <div className="opacity-50 pointer-events-none select-none">{children}</div>
      </div>
    )
  }

  return banner
}
