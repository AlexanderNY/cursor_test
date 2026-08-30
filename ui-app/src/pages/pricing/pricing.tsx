import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { PageHeader, PageContainer } from '@/components/ui'
import { useAuth } from '@/contexts/auth-context'
import { authService } from '@/services/auth-service'
import type { BillingPlanDefinition } from '@/types/auth'
import { getErrorMessage } from '@/services/api-client'

const HIGHLIGHT_FEATURES: Record<string, string[]> = {
  free: ['1 brand', '3 own channels', 'Inbox read', 'AI = 0'],
  standard: ['AI composer', 'Automations', 'Approval workflow', 'Team seats: 5'],
  full: ['Competitors', 'High AI quota', 'Webhooks + SLA', 'Team seats: 20'],
}

type PlanExtra = BillingPlanDefinition & {
  max_own_channels?: number
  max_brands?: number
  max_targets_per_job?: number
  max_automations?: number
  max_team_seats?: number
  ai_calls_month?: number
  schedule_horizon_days?: number
  stats_retention_days?: number
}

export function PricingPage() {
  const { isAuthenticated } = useAuth()
  const [plans, setPlans] = useState<PlanExtra[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [checkoutPlan, setCheckoutPlan] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setError('')
      try {
        const data = await authService.getBillingPlans()
        if (!cancelled) setPlans(data as PlanExtra[])
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

  async function startCheckout(code: string) {
    if (code !== 'standard' && code !== 'full') return
    if (!isAuthenticated) {
      window.location.href = `/sign-in?next=${encodeURIComponent('/pricing')}`
      return
    }
    setCheckoutPlan(code)
    setError('')
    try {
      const url = await authService.createCheckoutSession(code)
      window.location.href = url
    } catch (e) {
      setError(getErrorMessage(e))
      setCheckoutPlan(null)
    }
  }

  const sorted = [...plans].sort((a, b) => a.sort_order - b.sort_order)

  return (
    <PageContainer>
      <PageHeader
        title="Pricing"
        description="Free / Standard / Full — оформите подписку напрямую с сайта."
      />

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading plans…</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid gap-6 md:grid-cols-3">
        {sorted.map((p) => {
          const highlights = HIGHLIGHT_FEATURES[p.code] || []
          const canCheckout = p.code === 'standard' || p.code === 'full'
          return (
            <Card key={p.code} className="animate-slide-up flex flex-col">
              <CardHeader>
                <CardTitle className="text-xl">{p.display_name}</CardTitle>
                <CardDescription>{p.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 space-y-3 text-sm text-[var(--text-secondary)]">
                <ul className="space-y-1.5">
                  {highlights.map((h) => (
                    <li key={h} className="text-[var(--text-primary)]">
                      · {h}
                    </li>
                  ))}
                </ul>
                <div className="pt-2 border-t border-[var(--border-color)] space-y-1 text-xs">
                  <div>
                    Posts / month:{' '}
                    <span className="font-medium text-[var(--text-primary)]">
                      {p.monthly_posts_limit.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    Storage:{' '}
                    <span className="font-medium text-[var(--text-primary)]">{p.storage_gb_limit} GB</span>
                  </div>
                  {p.ai_calls_month != null && (
                    <div>
                      AI calls:{' '}
                      <span className="font-medium text-[var(--text-primary)]">{p.ai_calls_month}</span>
                    </div>
                  )}
                  {p.max_own_channels != null && (
                    <div>
                      Channels:{' '}
                      <span className="font-medium text-[var(--text-primary)]">{p.max_own_channels}</span>
                    </div>
                  )}
                  {p.max_brands != null && (
                    <div>
                      Brands:{' '}
                      <span className="font-medium text-[var(--text-primary)]">{p.max_brands}</span>
                    </div>
                  )}
                  {p.max_team_seats != null && (
                    <div>
                      Team seats:{' '}
                      <span className="font-medium text-[var(--text-primary)]">{p.max_team_seats}</span>
                    </div>
                  )}
                </div>

                <div className="pt-4 mt-auto">
                  {canCheckout ? (
                    <Button
                      type="button"
                      className="w-full"
                      isLoading={checkoutPlan === p.code}
                      disabled={checkoutPlan != null}
                      onClick={() => void startCheckout(p.code)}
                    >
                      Оформить
                    </Button>
                  ) : (
                    <Link
                      to={isAuthenticated ? '/profile?tab=billing' : '/sign-up'}
                      className="inline-flex w-full items-center justify-center font-medium rounded-xl px-6 py-3 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:border-primary-500/50"
                    >
                      {isAuthenticated ? 'Текущий план' : 'Начать бесплатно'}
                    </Link>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </PageContainer>
  )
}
