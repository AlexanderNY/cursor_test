import { Link } from 'react-router-dom'
import { Alert } from '@/components/ui/alert'
import { quotaResourceLabel } from '@/lib/quota'
import type { UsageMetric } from '@/types/smm'

type Props = {
  metrics?: UsageMetric[] | null
  /** Highlight a single metric key; otherwise show any near/over limit */
  focusKey?: string
  className?: string
}

function isNearOrOver(m: UsageMetric): boolean {
  if (m.used == null || m.limit <= 0) return m.limit === 0 && m.key === 'ai_calls_month'
  return m.used / m.limit >= 0.85
}

export function QuotaBanner({ metrics, focusKey, className = '' }: Props) {
  if (!metrics?.length) return null

  const candidates = focusKey
    ? metrics.filter((m) => m.key === focusKey)
    : metrics.filter(isNearOrOver)

  const critical = candidates.find((m) => m.used != null && m.limit > 0 && m.used >= m.limit)
  const near = candidates.find(isNearOrOver)
  const hit = critical || near
  if (!hit) return null

  const over = hit.used != null && hit.limit > 0 && hit.used >= hit.limit
  const label = quotaResourceLabel(hit.key)
  const usage =
    hit.used != null
      ? `${hit.used.toLocaleString()} / ${hit.limit.toLocaleString()}${hit.unit ? ` ${hit.unit}` : ''}`
      : `limit ${hit.limit}${hit.unit ? ` ${hit.unit}` : ''}`

  return (
    <Alert variant={over ? 'warning' : 'info'} className={className}>
      <span>
        {over ? `${label} limit reached` : `${label} nearly full`}: {usage}.{' '}
        <Link to="/pricing" className="underline text-primary-400 hover:text-primary-300">
          Upgrade
        </Link>
      </span>
    </Alert>
  )
}
