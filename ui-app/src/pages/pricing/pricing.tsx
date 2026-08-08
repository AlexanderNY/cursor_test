import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { PageHeader, PageContainer } from '@/components/ui'
import { authService } from '@/services/auth-service'
import type { BillingPlanDefinition } from '@/types/auth'

const FEATURE_LABELS: Record<string, string> = {
  ai_processing: 'AI processing',
  review_queue: 'Review queue',
  priority_queues: 'Priority queues',
  webhooks: 'Webhooks',
  sla_support: 'SLA support',
  inbox_read: 'Inbox read',
  inbox_reply: 'Inbox reply',
  inbox_redirect: 'Inbox redirect',
  multi_channel_send: 'Multi-channel send',
  schedule: 'Schedule',
  automations: 'Automations',
  ai_composer: 'AI composer',
  channel_stats: 'Channel stats',
  competitors: 'Competitors',
  approval_workflow: 'Approval workflow',
  best_times: 'Best times',
  auto_moderation: 'Auto moderation',
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
  csv_import_rows?: number
}

export function PricingPage() {
  const [plans, setPlans] = useState<PlanExtra[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

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

  const sorted = [...plans].sort((a, b) => a.sort_order - b.sort_order)

  return (
    <PageContainer>
      <PageHeader
        title="Pricing"
        description="Free / Standard / Full. Оплата и смена тарифа — Billing в профиле или Administration."
      />

      {loading && <p className="text-sm text-[var(--text-muted)]">Loading plans…</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid gap-6 md:grid-cols-3">
        {sorted.map((p) => (
          <Card key={p.code} className="animate-slide-up flex flex-col">
            <CardHeader>
              <CardTitle className="text-xl">{p.display_name}</CardTitle>
              <CardDescription>{p.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 space-y-2 text-sm text-[var(--text-secondary)]">
              <div>
                <span className="text-[var(--text-muted)]">Posts / month: </span>
                <span className="font-medium text-[var(--text-primary)]">
                  {p.monthly_posts_limit.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-[var(--text-muted)]">Storage: </span>
                <span className="font-medium text-[var(--text-primary)]">{p.storage_gb_limit} GB</span>
              </div>
              {p.max_own_channels != null && (
                <div>
                  <span className="text-[var(--text-muted)]">Own channels: </span>
                  <span className="font-medium text-[var(--text-primary)]">{p.max_own_channels}</span>
                </div>
              )}
              {p.max_brands != null && (
                <div>
                  <span className="text-[var(--text-muted)]">Brands: </span>
                  <span className="font-medium text-[var(--text-primary)]">{p.max_brands}</span>
                </div>
              )}
              {p.max_targets_per_job != null && (
                <div>
                  <span className="text-[var(--text-muted)]">Targets / job: </span>
                  <span className="font-medium text-[var(--text-primary)]">{p.max_targets_per_job}</span>
                </div>
              )}
              {p.schedule_horizon_days != null && (
                <div>
                  <span className="text-[var(--text-muted)]">Schedule horizon: </span>
                  <span className="font-medium text-[var(--text-primary)]">
                    {p.schedule_horizon_days} days
                  </span>
                </div>
              )}
              {p.ai_calls_month != null && (
                <div>
                  <span className="text-[var(--text-muted)]">AI calls / month: </span>
                  <span className="font-medium text-[var(--text-primary)]">{p.ai_calls_month}</span>
                </div>
              )}
              {p.stats_retention_days != null && (
                <div>
                  <span className="text-[var(--text-muted)]">Stats retention: </span>
                  <span className="font-medium text-[var(--text-primary)]">
                    {p.stats_retention_days} days
                  </span>
                </div>
              )}
              {p.max_team_seats != null && (
                <div>
                  <span className="text-[var(--text-muted)]">Team seats: </span>
                  <span className="font-medium text-[var(--text-primary)]">{p.max_team_seats}</span>
                </div>
              )}
              <ul className="list-disc list-inside space-y-1 pt-2 border-t border-[var(--border-color)]">
                {Object.entries(p.features).map(([k, v]) => (
                  <li key={k} className={v ? '' : 'opacity-60'}>
                    {FEATURE_LABELS[k] ?? k.replace(/_/g, ' ')}: {v ? 'yes' : 'no'}
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
