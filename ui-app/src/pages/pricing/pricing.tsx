import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { PageHeader, PageContainer } from '@/components/ui'
import { authService } from '@/services/auth-service'
import type { BillingPlanDefinition } from '@/types/auth'

export function PricingPage() {
  const [plans, setPlans] = useState<BillingPlanDefinition[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setError('')
      try {
        const data = await authService.getBillingPlans()
        if (!cancelled) setPlans(data)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load plans')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const sorted = [...plans].sort((a, b) => a.sort_order - b.sort_order)

  return (
    <PageContainer>
      <PageHeader
        title="Pricing"
        description="Тарифы и лимиты. Оплата и управление подпиской — в разделе Billing в профиле."
      />

      {loading && (
        <p className="text-sm text-[var(--text-muted)]">Loading plans…</p>
      )}
      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {sorted.map((p) => (
          <Card key={p.code} className="animate-slide-up flex flex-col">
            <CardHeader>
              <CardTitle className="text-xl">{p.display_name}</CardTitle>
              <CardDescription>{p.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 space-y-3 text-sm text-[var(--text-secondary)]">
              <div>
                <span className="text-[var(--text-muted)]">Posts / month: </span>
                <span className="font-medium text-[var(--text-primary)]">{p.monthly_posts_limit.toLocaleString()}</span>
              </div>
              <div>
                <span className="text-[var(--text-muted)]">Storage: </span>
                <span className="font-medium text-[var(--text-primary)]">{p.storage_gb_limit} GB</span>
              </div>
              <div>
                <span className="text-[var(--text-muted)]">Connected platforms: </span>
                <span className="font-medium text-[var(--text-primary)]">{p.max_connected_platforms}</span>
              </div>
              <ul className="list-disc list-inside space-y-1 pt-2 border-t border-[var(--border-color)]">
                {Object.entries(p.features).map(([k, v]) => (
                  <li key={k} className={v ? '' : 'opacity-60'}>
                    {k.replace(/_/g, ' ')}: {v ? 'yes' : 'no'}
                  </li>
                ))}
              </ul>
              <Link
                to="/profile?tab=billing"
                className="inline-block mt-4 text-primary-400 hover:underline text-sm font-medium"
              >
                Open billing →
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </PageContainer>
  )
}
