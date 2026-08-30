import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import type { QuotaErrorDetail } from '@/lib/quota'
import { quotaResourceLabel } from '@/lib/quota'

type Props = {
  open: boolean
  detail: QuotaErrorDetail | null
  onClose: () => void
}

export function QuotaUpgradeModal({ open, detail, onClose }: Props) {
  if (!open || !detail) return null

  const upgradeTo = detail.upgrade_url || '/pricing'
  const resourceLabel = detail.resource ? quotaResourceLabel(detail.resource) : null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="quota-upgrade-title"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl border border-[var(--border-color)] bg-[var(--bg-secondary)] p-6 shadow-xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="quota-upgrade-title" className="text-lg font-semibold text-[var(--text-primary)]">
          Plan limit reached
        </h2>
        <p className="text-sm text-[var(--text-secondary)]">{detail.message}</p>
        {(resourceLabel || detail.limit != null) && (
          <p className="text-xs text-[var(--text-muted)]">
            {resourceLabel}
            {detail.used != null && detail.limit != null
              ? `: ${detail.used} / ${detail.limit}`
              : detail.limit != null
                ? ` limit: ${detail.limit}`
                : ''}
          </p>
        )}
        <div className="flex flex-wrap gap-2 pt-2">
          <Link
            to={upgradeTo}
            className="inline-flex items-center justify-center font-medium rounded-xl px-5 py-2.5 text-sm bg-primary-500 text-white hover:bg-primary-600"
            onClick={onClose}
          >
            Upgrade plan
          </Link>
          <Button type="button" variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
