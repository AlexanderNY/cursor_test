import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/contexts/auth-context'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { authService } from '@/services/auth-service'
import type { BillingEventRow, BillingMeResponse } from '@/types/auth'

export function BillingTabContent() {
  const { user } = useAuth()
  const [me, setMe] = useState<BillingMeResponse | null>(null)
  const [events, setEvents] = useState<BillingEventRow[]>([])
  const [loading, setLoading] = useState(true)
  const [portalLoading, setPortalLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setError('')
      setLoading(true)
      try {
        const [billing, ev] = await Promise.all([
          authService.getBillingMe(),
          authService.getBillingEvents(20).catch(() => []),
        ])
        if (!cancelled) {
          setMe(billing)
          setEvents(ev)
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

  const plan = me?.plan

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Current plan</CardTitle>
        <CardDescription>Tariff, limits, and subscription status</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {loading && <p className="text-sm text-[var(--text-muted)]">Loading…</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex justify-between items-center py-3 border-b border-[var(--border-color)]">
          <span className="text-[var(--text-secondary)]">Tariff</span>
          <span className="font-medium capitalize">{me?.tariff ?? user?.tariff ?? 'free'}</span>
        </div>

        {plan && (
          <div className="space-y-2 text-sm text-[var(--text-secondary)]">
            <div className="flex justify-between">
              <span>Posts / month</span>
              <span className="text-[var(--text-primary)] font-medium">{plan.monthly_posts_limit.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Storage</span>
              <span className="text-[var(--text-primary)] font-medium">{plan.storage_gb_limit} GB</span>
            </div>
            <div className="flex justify-between">
              <span>Platforms</span>
              <span className="text-[var(--text-primary)] font-medium">{plan.max_connected_platforms}</span>
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
                {new Date(me.subscription_current_period_end).toLocaleString()}
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

        <div className="flex flex-wrap gap-3">
          {me?.stripe_portal_available ? (
            <Button type="button" onClick={openPortal} isLoading={portalLoading}>
              Manage subscription
            </Button>
          ) : (
            <p className="text-xs text-[var(--text-muted)]">
              Stripe Customer Portal becomes available after checkout links a customer to your account.
            </p>
          )}
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
                    {new Date(ev.created_at).toLocaleString()}
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
