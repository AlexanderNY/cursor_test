import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { PageHeader, PageContainer } from '@/components/ui'
import { useAuth } from '@/contexts/auth-context'
import { useToast } from '@/contexts/toast-context'
import { authService } from '@/services/auth-service'
import type { BillingPlanDefinition, BillingPlanRequest } from '@/types/auth'
import { getErrorMessage } from '@/services/api-client'
import { formatRub } from '@/lib/billing'

const HIGHLIGHT_FEATURES: Record<string, string[]> = {
  free: ['1 brand', '3 own channels', 'Schedule 7d', '1 content series', 'AI = 0'],
  standard: ['AI composer', 'Schedule 30d', '10 series', 'Approval + Team 5'],
  full: ['Competitors', 'Schedule 90d', '50 series', 'Webhooks + SLA'],
}

type PlanExtra = BillingPlanDefinition & {
  max_own_channels?: number
  max_competitor_channels?: number
  max_brands?: number
  max_targets_per_job?: number
  max_automations?: number
  max_team_seats?: number
  max_content_series?: number
  ai_calls_month?: number
  schedule_horizon_days?: number
  stats_retention_days?: number
}

export function PricingPage() {
  const { isAuthenticated, user } = useAuth()
  const { addToast } = useToast()
  const [plans, setPlans] = useState<PlanExtra[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [requestingPlan, setRequestingPlan] = useState<string | null>(null)
  const [promoCode, setPromoCode] = useState('')
  const [promoHint, setPromoHint] = useState('')
  const [pending, setPending] = useState<BillingPlanRequest | null>(null)

  const currentTariff = (user?.tariff ?? 'free').toLowerCase()

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setError('')
      try {
        const data = await authService.getBillingPlans()
        if (!cancelled) setPlans(data as PlanExtra[])
        if (isAuthenticated) {
          const me = await authService.getBillingMe().catch(() => null)
          if (!cancelled) setPending(me?.pending_request ?? null)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load plans')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [isAuthenticated])

  async function applyPromoPreview(plan: string) {
    const code = promoCode.trim()
    if (!code || !isAuthenticated) {
      setPromoHint('')
      return
    }
    try {
      const preview = await authService.previewPromo(code, plan)
      setPromoHint(
        `Промокод ${preview.code}: ${formatRub(preview.list_price, preview.currency)} → ${formatRub(preview.final_price, preview.currency)}`,
      )
    } catch (e) {
      setPromoHint(getErrorMessage(e))
    }
  }

  async function requestPlan(code: string) {
    if (code !== 'standard' && code !== 'full') return
    if (!isAuthenticated) {
      window.location.href = `/sign-in?next=${encodeURIComponent('/pricing')}`
      return
    }
    setRequestingPlan(code)
    setError('')
    try {
      const req = await authService.createPlanRequest(code, promoCode.trim() || undefined)
      setPending(req)
      addToast(`Заявка на ${code} создана. Администратор отправит счёт или включит тариф.`)
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setRequestingPlan(null)
    }
  }

  const sorted = [...plans].sort((a, b) => a.sort_order - b.sort_order)

  return (
    <PageContainer maxWidth="wide">
      <PageHeader
        title="Pricing"
        description="Free / Standard / Full — оставьте заявку, счёт придёт на почту. Можно указать промокод."
      />

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading plans…</p>}
      {error && <Alert variant="error">{error}</Alert>}
      {pending && (
        <Alert variant="info">
          Открытая заявка: {pending.current_tariff} → {pending.requested_tariff},{' '}
          {formatRub(pending.final_price, pending.currency)} · статус {pending.status}.{' '}
          <Link to="/profile?tab=billing" className="underline">
            Биллинг
          </Link>
        </Alert>
      )}

      {isAuthenticated && (
        <div className="max-w-md">
          <Input
            label="Промокод"
            value={promoCode}
            onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
            onBlur={() => void applyPromoPreview('standard')}
            placeholder="SUMMER20"
          />
          {promoHint && <p className="text-xs text-[var(--text-muted)] mt-1">{promoHint}</p>}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        {sorted.map((p) => {
          const highlights = HIGHLIGHT_FEATURES[p.code] || []
          const canRequest = p.code === 'standard' || p.code === 'full'
          const isCurrent = currentTariff === p.code || (currentTariff === 'basic' && p.code === 'standard')
          const price = p.price_monthly ?? 0
          return (
            <Card key={p.code} className="animate-slide-up flex flex-col">
              <CardHeader>
                <CardTitle className="text-xl">{p.display_name}</CardTitle>
                <CardDescription>{p.description}</CardDescription>
                <p className="text-2xl font-semibold text-[var(--text-primary)] pt-2">
                  {price > 0 ? `${formatRub(price, p.currency)} / мес` : 'Бесплатно'}
                </p>
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
                  {p.max_competitor_channels != null && (
                    <div>
                      Competitors:{' '}
                      <span className="font-medium text-[var(--text-primary)]">
                        {p.max_competitor_channels}
                      </span>
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
                  {isCurrent ? (
                    <Link
                      to="/profile?tab=billing"
                      className="inline-flex w-full items-center justify-center font-medium rounded-xl px-6 py-3 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:border-primary-500/50"
                    >
                      Текущий план
                    </Link>
                  ) : canRequest ? (
                    <Button
                      type="button"
                      className="w-full"
                      isLoading={requestingPlan === p.code}
                      disabled={requestingPlan != null}
                      onClick={() => void requestPlan(p.code)}
                    >
                      Запросить тариф
                    </Button>
                  ) : (
                    <Link
                      to={isAuthenticated ? '/profile?tab=billing' : '/sign-up'}
                      className="inline-flex w-full items-center justify-center font-medium rounded-xl px-6 py-3 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:border-primary-500/50"
                    >
                      {isAuthenticated ? 'Остаться на Free' : 'Начать бесплатно'}
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
