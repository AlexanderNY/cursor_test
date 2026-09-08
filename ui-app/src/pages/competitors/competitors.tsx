import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageContainer, PageHeader } from '@/components/ui'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Alert } from '@/components/ui/alert'
import { PlanGate } from '@/components/billing/PlanGate'
import { BestTimesHeatmap } from '@/pages/smm-analytics/components/analytics-charts'
import { useBrand } from '@/contexts/brand-context'
import { smmService } from '@/services/smm-service'
import type {
  BrandChannel,
  CompetitorCompare,
  CompetitorDigest,
  CompetitorIdea,
  CompetitorInsights,
  CompetitorPost,
} from '@/types/smm'
import { getErrorMessage } from '@/services/api-client'
import { formatDateTime } from '@/utils/date'

type CompNetwork = 'tg' | 'vk' | 'url'
const WEEKDAYS = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

function ideaDraftText(idea: CompetitorIdea): string {
  const parts = [idea.title]
  if (idea.hook) parts.push(idea.hook)
  if (idea.angle) parts.push(idea.angle)
  return parts.join('\n\n')
}

export function CompetitorsPage() {
  const { selectedBrandId, channels, refreshChannels } = useBrand()
  const [canCompetitors, setCanCompetitors] = useState(true)
  const [error, setError] = useState('')
  const [compNetwork, setCompNetwork] = useState<CompNetwork>('tg')
  const [compId, setCompId] = useState('')
  const [compUrl, setCompUrl] = useState('')
  const [compTitle, setCompTitle] = useState('')
  const [alertOnAdd, setAlertOnAdd] = useState(true)
  const [selected, setSelected] = useState<BrandChannel | null>(null)
  const [posts, setPosts] = useState<CompetitorPost[]>([])
  const [digest, setDigest] = useState<CompetitorDigest | null>(null)
  const [compare, setCompare] = useState<CompetitorCompare | null>(null)
  const [insights, setInsights] = useState<CompetitorInsights | null>(null)
  const [ideas, setIdeas] = useState<CompetitorIdea[]>([])
  const [ideasFallback, setIdeasFallback] = useState(false)
  const [digestPeriod, setDigestPeriod] = useState<'24h' | '7d'>('24h')
  const [insightsPeriod, setInsightsPeriod] = useState<'7d' | '30d'>('7d')
  const [viralOnly, setViralOnly] = useState(false)
  const [busy, setBusy] = useState(false)

  const competitors = useMemo(
    () => channels.filter((c) => c.role === 'competitor'),
    [channels],
  )

  const visiblePosts = useMemo(() => {
    if (!viralOnly) return posts
    const views = posts
      .map((p) => p.views ?? 0)
      .filter((v) => v > 0)
      .sort((a, b) => a - b)
    const median = views.length ? views[Math.floor(views.length / 2)] : 0
    const threshold = Math.max(500, median * 3)
    return posts.filter((p) => (p.views ?? 0) >= threshold)
  }, [posts, viralOnly])

  useEffect(() => {
    void (async () => {
      try {
        const plan = await smmService.getPlan().catch(() => null)
        const feats = (plan?.limits?.features || {}) as Record<string, boolean>
        setCanCompetitors(Boolean(feats.competitors))
      } catch {
        /* ignore */
      }
    })()
  }, [])

  async function handleAdd() {
    if (!selectedBrandId) {
      setError('Сначала выберите бренд')
      return
    }
    if (compNetwork === 'url' && !compUrl.trim()) {
      setError('Укажите URL для мониторинга')
      return
    }
    if (compNetwork !== 'url' && !compId.trim()) {
      setError('Укажите External ID')
      return
    }
    setBusy(true)
    setError('')
    try {
      await smmService.addCompetitor({
        brand_id: selectedBrandId,
        network: compNetwork,
        external_id: compNetwork === 'url' ? undefined : compId.trim(),
        url: compNetwork === 'url' ? compUrl.trim() : undefined,
        title: compTitle.trim() || undefined,
        alert_enabled: alertOnAdd,
      })
      setCompId('')
      setCompUrl('')
      setCompTitle('')
      await refreshChannels()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function selectCompetitor(ch: BrandChannel) {
    setSelected(ch)
    setDigest(null)
    setCompare(null)
    setInsights(null)
    setIdeas([])
    setIdeasFallback(false)
    setError('')
    try {
      setPosts(await smmService.competitorPosts(ch.id))
      setInsights(await smmService.competitorInsights(ch.id, insightsPeriod, true))
    } catch (err) {
      setError(getErrorMessage(err))
      setPosts([])
    }
  }

  async function loadInsights() {
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      setInsights(await smmService.competitorInsights(selected.id, insightsPeriod, true))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function loadDigest() {
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      setDigest(await smmService.competitorDigest(selected.id, digestPeriod, true))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function loadCompare() {
    if (!selected || !selectedBrandId) return
    setBusy(true)
    setError('')
    try {
      setCompare(await smmService.competitorCompare(selectedBrandId, selected.id, '7d'))
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function loadIdeas() {
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      const res = await smmService.competitorIdeas(selected.id, {
        brand_id: selectedBrandId ?? undefined,
        limit: 6,
      })
      setIdeas(res.ideas || [])
      setIdeasFallback(Boolean(res.fallback))
      if (res.message && !(res.ideas || []).length) setError(res.message)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  async function toggleAlerts(ch: BrandChannel) {
    setBusy(true)
    setError('')
    try {
      const updated = await smmService.updateCompetitor(ch.id, {
        alert_enabled: !ch.alert_enabled,
      })
      await refreshChannels()
      if (selected?.id === ch.id) setSelected(updated)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  if (!canCompetitors) {
    return (
      <PageContainer>
        <PageHeader
          title="Competitors"
          description="Мониторинг конкурентов: дайджесты, сравнение и алерты о новых постах"
        />
        <PlanGate allowed={false} featureLabel="Competitors">
          <div />
        </PlanGate>
      </PageContainer>
    )
  }

  const cadence = insights?.cadence
  const peakDayIdx = cadence
    ? cadence.weekday_histogram.reduce(
        (best, n, i, arr) => (n > arr[best] ? i : best),
        0,
      )
    : 0
  const peakHourIdx = cadence
    ? cadence.hour_histogram.reduce((best, n, i, arr) => (n > arr[best] ? i : best), 0)
    : 0

  return (
    <PageContainer>
      <PageHeader
        title="Competitors"
        description="Частота, best time, темы, виральные алерты и идеи для постов"
      />
      {error && <Alert variant="error">{error}</Alert>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Добавить конкурента</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedBrandId && (
              <Alert variant="error">Сначала выберите бренд</Alert>
            )}
            <div className="grid gap-2 sm:grid-cols-2">
              <select
                className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2"
                value={compNetwork}
                onChange={(e) => setCompNetwork(e.target.value as CompNetwork)}
              >
                <option value="tg">Telegram</option>
                <option value="vk">VKontakte</option>
                <option value="url">URL / RSS radar</option>
              </select>
              {compNetwork === 'url' ? (
                <Input
                  value={compUrl}
                  onChange={(e) => setCompUrl(e.target.value)}
                  placeholder="https://example.com/feed"
                />
              ) : (
                <Input
                  value={compId}
                  onChange={(e) => setCompId(e.target.value)}
                  placeholder="External ID / @username"
                />
              )}
              <Input
                value={compTitle}
                onChange={(e) => setCompTitle(e.target.value)}
                placeholder="Title"
              />
              <Button onClick={() => void handleAdd()} disabled={!selectedBrandId || busy}>
                Add
              </Button>
            </div>
            <label className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <input
                type="checkbox"
                checked={alertOnAdd}
                onChange={(e) => setAlertOnAdd(e.target.checked)}
              />
              Алерты о новых и виральных постах → Inbox
            </label>

            {competitors.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)] py-4">
                Пока нет конкурентов. Добавьте TG/VK канал или URL-radar.
              </p>
            ) : (
              <ul className="space-y-2">
                {competitors.map((c) => (
                  <li key={c.id}>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className={`flex-1 text-left rounded border px-3 py-2 text-sm hover:bg-[var(--bg-tertiary)] ${
                          selected?.id === c.id
                            ? 'border-primary-400'
                            : 'border-[var(--border-color)]'
                        }`}
                        onClick={() => void selectCompetitor(c)}
                      >
                        <span className="uppercase text-[var(--text-muted)] mr-2">
                          {c.network}
                        </span>
                        {c.title || c.external_id}
                      </button>
                      <Button
                        variant="secondary"
                        className="shrink-0 text-xs"
                        disabled={busy}
                        onClick={() => void toggleAlerts(c)}
                        title="Алерты в Inbox"
                      >
                        {c.alert_enabled ? 'Alerts on' : 'Alerts off'}
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>
              Лента
              {selected ? ` · ${selected.title || selected.external_id}` : ''}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selected && (
              <p className="text-sm text-[var(--text-muted)]">
                Выберите конкурента слева, чтобы увидеть insights, посты и идеи.
              </p>
            )}
            {selected && (
              <>
                <div className="flex flex-wrap gap-2">
                  <select
                    className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={insightsPeriod}
                    onChange={(e) => setInsightsPeriod(e.target.value as '7d' | '30d')}
                  >
                    <option value="7d">Insights 7d</option>
                    <option value="30d">Insights 30d</option>
                  </select>
                  <Button disabled={busy} onClick={() => void loadInsights()}>
                    Insights
                  </Button>
                  <select
                    className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
                    value={digestPeriod}
                    onChange={(e) => setDigestPeriod(e.target.value as '24h' | '7d')}
                  >
                    <option value="24h">Digest 24h</option>
                    <option value="7d">Digest 7d</option>
                  </select>
                  <Button disabled={busy} onClick={() => void loadDigest()}>
                    Digest
                  </Button>
                  <Button
                    variant="secondary"
                    disabled={busy || !selectedBrandId}
                    onClick={() => void loadCompare()}
                  >
                    Compare vs brand
                  </Button>
                  <Button variant="secondary" disabled={busy} onClick={() => void loadIdeas()}>
                    Ideas
                  </Button>
                  <label className="flex items-center gap-2 text-sm self-center text-[var(--text-muted)]">
                    <input
                      type="checkbox"
                      checked={viralOnly}
                      onChange={(e) => setViralOnly(e.target.checked)}
                    />
                    Viral only
                  </label>
                  <Link
                    to={`/inbox`}
                    className="text-sm self-center text-primary-400 hover:underline"
                  >
                    Inbox alerts
                  </Link>
                  <Link
                    to={`/channels/${selected.id}`}
                    className="text-sm self-center text-primary-400 hover:underline"
                  >
                    Channel settings
                  </Link>
                  <Link
                    to="/analytics?tab=competitors"
                    className="text-sm self-center text-primary-400 hover:underline"
                  >
                    Analytics tab
                  </Link>
                </div>

                {insights && cadence && (
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded border border-[var(--border-color)] p-3 text-sm">
                      <p className="text-xs text-[var(--text-muted)]">Posts / day</p>
                      <p className="text-lg font-semibold">
                        {cadence.posts_per_day ?? '—'}
                      </p>
                      <p className="text-xs text-[var(--text-muted)]">
                        {cadence.posts_count} posts · {insights.period}
                      </p>
                    </div>
                    <div className="rounded border border-[var(--border-color)] p-3 text-sm">
                      <p className="text-xs text-[var(--text-muted)]">Peak day / hour</p>
                      <p className="text-lg font-semibold">
                        {WEEKDAYS[peakDayIdx]} · {peakHourIdx}:00
                      </p>
                      <p className="text-xs text-[var(--text-muted)]">
                        median gap{' '}
                        {cadence.interval_hours_median != null
                          ? `${cadence.interval_hours_median}h`
                          : '—'}
                      </p>
                    </div>
                    <div className="rounded border border-[var(--border-color)] p-3 text-sm">
                      <p className="text-xs text-[var(--text-muted)] mb-1">Themes</p>
                      {insights.themes.length === 0 ? (
                        <p className="text-[var(--text-muted)]">Нет тем</p>
                      ) : (
                        <p>
                          {insights.themes
                            .slice(0, 4)
                            .map((t) => `${t.theme}(${t.count})`)
                            .join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {insights && insights.best_slots.length > 0 && (
                  <div className="rounded border border-[var(--border-color)] p-3 space-y-2">
                    <p className="text-xs text-[var(--text-muted)]">
                      Best posting times (competitor)
                    </p>
                    <BestTimesHeatmap slots={insights.best_slots} />
                  </div>
                )}

                {digest && (
                  <div className="rounded border border-[var(--border-color)] p-3 space-y-2">
                    <p className="text-xs text-[var(--text-muted)]">
                      Digest {digest.period} · {digest.posts_count} posts
                      {digest.fallback ? ' · AI fallback' : ''}
                    </p>
                    <p className="text-sm whitespace-pre-wrap">
                      {digest.summary || 'Нет текста для суммаризации'}
                    </p>
                  </div>
                )}

                {compare && (
                  <div className="rounded border border-[var(--border-color)] p-3 text-sm space-y-1">
                    <p>
                      Own: {compare.own.posts_count} posts ·{' '}
                      {compare.own.posts_per_day ?? '—'} /day · avg{' '}
                      {compare.own.avg_length} chars
                    </p>
                    <p>
                      Competitor: {compare.competitor.posts_count} posts ·{' '}
                      {compare.competitor.posts_per_day ?? '—'} /day · avg{' '}
                      {compare.competitor.avg_length} chars
                    </p>
                    {compare.top_themes.length > 0 && (
                      <p className="text-[var(--text-muted)]">
                        Themes:{' '}
                        {compare.top_themes.map((t) => `${t.theme}(${t.count})`).join(', ')}
                      </p>
                    )}
                    {(compare.slot_overlap || []).length > 0 && (
                      <p className="text-[var(--text-muted)]">
                        Overlap slots:{' '}
                        {compare.slot_overlap!
                          .slice(0, 5)
                          .map(
                            (s) =>
                              `${WEEKDAYS[s.weekday] ?? s.weekday} ${s.hour}:00`,
                          )
                          .join(', ')}
                      </p>
                    )}
                  </div>
                )}

                {ideas.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs text-[var(--text-muted)]">
                      Ideas for your brand
                      {ideasFallback ? ' · heuristic fallback' : ''}
                    </p>
                    {ideas.map((idea, idx) => (
                      <div
                        key={`${idea.title}-${idx}`}
                        className="rounded border border-[var(--border-color)] p-3 text-sm space-y-1"
                      >
                        <div className="flex justify-between gap-2">
                          <p className="font-medium">{idea.title}</p>
                          <span className="text-xs text-[var(--text-muted)] shrink-0">
                            {idea.theme}
                          </span>
                        </div>
                        {idea.hook && (
                          <p className="text-[var(--text-muted)]">Hook: {idea.hook}</p>
                        )}
                        {idea.angle && <p>{idea.angle}</p>}
                        <Link
                          to={`/posts?draft=${encodeURIComponent(ideaDraftText(idea))}`}
                          className="inline-block text-xs text-primary-400 hover:underline"
                        >
                          В черновик
                        </Link>
                      </div>
                    ))}
                  </div>
                )}

                <ul className="space-y-2 max-h-[28rem] overflow-auto">
                  {visiblePosts.map((p) => {
                    const views = p.views ?? 0
                    const isViral =
                      insights != null &&
                      views >=
                        Math.max(
                          500,
                          (() => {
                            const sorted = posts
                              .map((x) => x.views ?? 0)
                              .filter((v) => v > 0)
                              .sort((a, b) => a - b)
                            return sorted.length
                              ? sorted[Math.floor(sorted.length / 2)] * 3
                              : 0
                          })(),
                        )
                    return (
                      <li
                        key={p.id}
                        className="rounded border border-[var(--border-color)] px-3 py-2 text-sm"
                      >
                        <div className="flex justify-between gap-2 text-xs text-[var(--text-muted)] mb-1">
                          <span>{formatDateTime(p.posted_at || p.collected_at)}</span>
                          <span className="flex items-center gap-2">
                            {isViral && (
                              <span className="rounded bg-amber-500/20 text-amber-300 px-1.5 py-0.5">
                                Viral
                              </span>
                            )}
                            {views} views · {p.likes ?? 0} likes
                          </span>
                        </div>
                        <p className="whitespace-pre-wrap line-clamp-6">{p.text || '—'}</p>
                        {p.url ? (
                          <a
                            href={p.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-primary-400 hover:underline"
                          >
                            Open
                          </a>
                        ) : null}
                      </li>
                    )
                  })}
                  {visiblePosts.length === 0 && (
                    <p className="text-sm text-[var(--text-muted)]">
                      {viralOnly
                        ? 'Нет виральных постов по текущему порогу'
                        : 'Снимки появятся после sync коллектора'}
                    </p>
                  )}
                </ul>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
