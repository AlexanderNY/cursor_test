import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { QuotaBanner } from '@/components/billing/QuotaBanner'
import { authService } from '@/services/auth-service'
import { smmService } from '@/services/smm-service'
import type { BillingEventRow, BillingMeResponse } from '@/types/auth'
import type { UsageSummary } from '@/types/smm'
import { quotaResourceLabel } from '@/lib/quota'
import { formatDateTime } from '@/utils/date'
import { getErrorMessage } from '@/services/api-client'
import { formatRub, PLAN_REQUEST_STATUS_LABEL } from '@/lib/billing'

export function BillingTabContent() {
  const { user } = useAuth()
  const [searchParams] = useSearchParams()
  const [me, setMe] = useState<BillingMeResponse | null>(null)
  const [events, setEvents] = useState<BillingEventRow[]>([])
  const [usage, setUsage] = useState<UsageSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [portalLoading, setPortalLoading] = useState(false)
  const [checkoutPlan, setCheckoutPlan] = useState<'standard' | 'full' | null>(null)
  const [requestingPlan, setRequestingPlan] = useState<'standard' | 'full' | null>(null)
  const [promoCode, setPromoCode] = useState('')
  const [error, setError] = useState('')

  const checkoutFlash = searchParams.get('checkout')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setError('')
      setLoading(true)
      try {
        const [billing, ev, usageSummary] = await Promise.all([
          authService.getBillingMe(),
          authService.getBillingEvents(20).catch(() => []),
          smmService.getUsageSummary().catch(() => null),
        ])
        if (!cancelled) {
          setMe(billing)
          setEvents(ev)
          setUsage(usageSummary)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load billing')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [user?.id])

  async function openPortal() {
    setPortalLoading(true)
    setError('')
    try {
      const url = await authService.createBillingPortalSession()
      window.location.href = url
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not open billing portal')
    } finally {
      setPortalLoading(false)
    }
  }

  async function startCheckout(plan: 'standard' | 'full') {
    setCheckoutPlan(plan)
    setError('')
    try {
      const url = await authService.createCheckoutSession(plan)
      window.location.href = url
    } catch (e) {
      setError(getErrorMessage(e))
      setCheckoutPlan(null)
    }
  }

  async function requestPlan(plan: 'standard' | 'full') {
    setRequestingPlan(plan)
    setError('')
    try {
      const req = await authService.createPlanRequest(plan, promoCode.trim() || undefined)
      setMe((prev) => (prev ? { ...prev, pending_request: req } : prev))
    } catch (e) {
      setError(getErrorMessage(e))
    } finally {
      setRequestingPlan(null)
    }
  }

  const plan = me?.plan
  const tariff = (me?.tariff ?? user?.tariff ?? 'free').toLowerCase()
  const showUpgrade = tariff === 'free' || tariff === 'standard' || tariff === 'basic'

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Current plan</CardTitle>
        <CardDescription>Тариф, заявки на смену плана и использование лимитов</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}

        {checkoutFlash === 'success' && (
          <Alert variant="success">
            Checkout completed. Plan updates after Stripe webhook confirmation (usually seconds).
          </Alert>
        )}
        {checkoutFlash === 'cancel' && (
          <Alert variant="info">Checkout cancelled. You can try again anytime.</Alert>
        )}

        {me?.pending_request && (
          <Alert variant="info">
            Заявка #{me.pending_request.id}: {me.pending_request.current_tariff} →{' '}
            {me.pending_request.requested_tariff},{' '}
            {formatRub(me.pending_request.final_price, me.pending_request.currency)}
            {me.pending_request.promo_code ? ` · промокод ${me.pending_request.promo_code}` : ''}. Статус:{' '}
            {PLAN_REQUEST_STATUS_LABEL[me.pending_request.status] ?? me.pending_request.status}.
          </Alert>
        )}

        <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
          <span className="text-[var(--text-secondary)]">Tariff</span>
          <span className="font-medium capitalize">{tariff}</span>
        </div>

        {usage?.metrics && (
          <div className="space-y-3">
            <QuotaBanner metrics={usage.metrics} />
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">Usage this period</h3>
            <div className="space-y-2 text-sm">
              {usage.metrics.map((m) => (
                <div
                  key={m.key}
                  className="flex justify-between gap-2 text-[var(--text-secondary)]"
                >
                  <span>{quotaResourceLabel(m.key)}</span>
                  <span className="text-[var(--text-primary)] font-medium tabular-nums">
                    {m.used != null
                      ? `${m.used.toLocaleString()} / ${m.limit.toLocaleString()}`
                      : `— / ${m.limit.toLocaleString()}`}
                    {m.unit ? ` ${m.unit}` : ''}
                  </span>
                </div>
              ))}
            </div>
            {usage.period && (
              <p className="text-xs text-[var(--text-muted)]">Period: {usage.period}</p>
            )}
          </div>
        )}

        {!usage?.metrics && plan && (
          <div className="space-y-2 text-sm text-[var(--text-secondary)]">
            <div className="flex justify-between">
              <span>Posts / month</span>
              <span className="text-[var(--text-primary)] font-medium">
                {plan.monthly_posts_limit.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Storage</span>
              <span className="text-[var(--text-primary)] font-medium">{plan.storage_gb_limit} GB</span>
            </div>
          </div>
        )}

        <div className="space-y-2 text-sm border-t border-[var(--border-color)] pt-4">
          <div className="flex justify-between">
            <span className="text-[var(--text-secondary)]">Subscription status</span>
            <span className="font-medium">{me?.subscription_status ?? '—'}</span>
          </div>
          {me?.subscription_current_period_end && (
            <div className="flex justify-between">
              <span className="text-[var(--text-secondary)]">Current period ends</span>
              <span className="font-medium">
                {formatDateTime(me.subscription_current_period_end)}
              </span>
            </div>
          )}
          {me?.billing_provider && (
            <div className="flex justify-between">
              <span className="text-[var(--text-secondary)]">Provider</span>
              <span className="font-medium">{me.billing_provider}</span>
            </div>
          )}
        </div>

        <div className="space-y-3 border-t border-[var(--border-color)] pt-4">
          {showUpgrade && (
            <>
              <Input
                label="Промокод"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
                placeholder="Необязательно"
              />
              <div className="flex flex-wrap gap-3">
                {(tariff === 'free' || tariff === 'basic') && (
                  <Button
                    type="button"
                    onClick={() => void requestPlan('standard')}
                    isLoading={requestingPlan === 'standard'}
                    disabled={requestingPlan != null}
                  >
                    Запросить Standard
                  </Button>
                )}
                <Button
                  type="button"
                  variant={tariff === 'standard' ? 'primary' : 'secondary'}
                  onClick={() => void requestPlan('full')}
                  isLoading={requestingPlan === 'full'}
                  disabled={requestingPlan != null}
                >
                  Запросить Full
                </Button>
              </div>
            </>
          )}
          {me?.stripe_checkout_available && showUpgrade && (
            <div className="flex flex-wrap gap-3">
              {(tariff === 'free' || tariff === 'basic') && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void startCheckout('standard')}
                  isLoading={checkoutPlan === 'standard'}
                  disabled={checkoutPlan != null}
                >
                  Оплатить картой Standard
                </Button>
              )}
              <Button
                type="button"
                variant="secondary"
                onClick={() => void startCheckout('full')}
                isLoading={checkoutPlan === 'full'}
                disabled={checkoutPlan != null}
              >
                Оплатить картой Full
              </Button>
            </div>
          )}
          {me?.stripe_portal_available ? (
            <Button type="button" variant="secondary" onClick={openPortal} isLoading={portalLoading}>
              Manage subscription
            </Button>
          ) : null}
          <Link
            to="/pricing"
            className="inline-flex items-center justify-center font-medium rounded-xl px-6 py-3 text-sm bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--bg-secondary)] hover:border-primary-500/50"
          >
            Compare plans
          </Link>
        </div>

        {events.length > 0 && (
          <div className="border-t border-[var(--border-color)] pt-4">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">Recent billing events</h3>
            <ul className="text-xs text-[var(--text-secondary)] space-y-1">
              {events.map((ev) => (
                <li key={ev.id} className="flex justify-between gap-2">
                  <span>{ev.event_type}</span>
                  <span className="text-[var(--text-muted)] whitespace-nowrap">
                    {formatDateTime(ev.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
