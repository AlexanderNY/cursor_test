import { useCallback, useEffect, useMemo, useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { telegramService } from '@/services/telegram-service'
import type {
  TgAnalyticsOverview,
  TgAnalyticsChannelItem,
  TgAnalyticsKeywordItem,
  TgAnalyticsTimelinePoint,
  TgAnalyticsSentimentBreakdown,
  TgAnalyticsEngagement,
  TgAnalyticsHealth,
} from '@/types/telegram'
import { formatDateTime } from '@/utils/date'

const FILTERS_KEY = 'tg-analytics-filters'

type SavedFilters = {
  period: string
}

function loadSavedFilters(): SavedFilters {
  try {
    const raw = localStorage.getItem(FILTERS_KEY)
    if (!raw) return { period: '7d' }
    const parsed = JSON.parse(raw) as SavedFilters
    return { period: parsed.period || '7d' }
  } catch {
    return { period: '7d' }
  }
}

function sameChatId(a?: string | null, b?: string | null): boolean {
  if (!a || !b) return false
  const x = String(a).trim()
  const y = String(b).trim()
  if (x === y) return true
  try {
    return Number(x) === Number(y)
  } catch {
    return false
  }
}

function EmptyState({ label }: { label: string }) {
  return (
    <p className="text-sm text-[var(--text-muted)] py-4 text-center border border-dashed border-[var(--border-color)] rounded-lg">
      {label}
    </p>
  )
}

export function TelegramAnalyticsPanel({
  chatIdFilter = null,
}: {
  chatIdFilter?: string | null
}) {
  const initial = useMemo(() => loadSavedFilters(), [])
  const [period, setPeriod] = useState(initial.period)
  const [isLoading, setIsLoading] = useState(true)
  const [overview, setOverview] = useState<TgAnalyticsOverview | null>(null)
  const [channels, setChannels] = useState<TgAnalyticsChannelItem[]>([])
  const [keywords, setKeywords] = useState<TgAnalyticsKeywordItem[]>([])
  const [timeline, setTimeline] = useState<TgAnalyticsTimelinePoint[]>([])
  const [sentiment, setSentiment] = useState<TgAnalyticsSentimentBreakdown | null>(null)
  const [engagement, setEngagement] = useState<TgAnalyticsEngagement | null>(null)
  const [health, setHealth] = useState<TgAnalyticsHealth | null>(null)

  useEffect(() => {
    localStorage.setItem(FILTERS_KEY, JSON.stringify({ period }))
  }, [period])

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      const chatId = chatIdFilter || undefined
      const [ov, ch, kw, tl, sent, eng, hl] = await Promise.all([
        telegramService.getAnalyticsOverview(period, chatId),
        telegramService.getAnalyticsChannels(period, 10, chatId),
        telegramService.getAnalyticsKeywords(period, 20, chatId),
        telegramService.getAnalyticsTimeline(period, 'hour', chatId),
        telegramService.getAnalyticsSentiment(period, chatId),
        telegramService.getAnalyticsEngagement(period, 10, chatId),
        telegramService.getAnalyticsHealth('24h'),
      ])
      setOverview(ov)
      setChannels(ch)
      setKeywords(kw)
      setTimeline(tl)
      setSentiment(sent)
      setEngagement(eng)
      setHealth(hl)
    } catch (err) {
      console.warn('Telegram analytics load failed', err)
    } finally {
      setIsLoading(false)
    }
  }, [period, chatIdFilter])

  useEffect(() => {
    let cancelled = false
    void (async () => {
      if (cancelled) return
      await load()
    })()
    return () => {
      cancelled = true
    }
  }, [load])

  const visibleChannels = useMemo(() => {
    if (!chatIdFilter) return channels
    return channels.filter((c) => sameChatId(c.chat_id, chatIdFilter))
  }, [channels, chatIdFilter])

  const hasData =
    (overview?.messages_collected ?? 0) > 0 ||
    (overview?.alerts_sent ?? 0) > 0 ||
    visibleChannels.length > 0 ||
    keywords.length > 0

  async function handleExport() {
    try {
      const blob = await telegramService.exportAnalyticsCsv(period, chatIdFilter || undefined)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tg-analytics-${period}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.warn('CSV export failed', err)
    }
  }

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle>Telegram Analytics</CardTitle>
            <CardDescription>
              Метрики сбора и engagement
              {chatIdFilter ? ` · канал ${chatIdFilter}` : ''}
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <select
              className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-sm"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
            >
              <option value="24h">24 hours</option>
              <option value="7d">7 days</option>
              <option value="30d">30 days</option>
            </select>
            <Button type="button" variant="secondary" onClick={() => void handleExport()}>
              Export CSV
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading analytics...</div>
        ) : !hasData ? (
          <EmptyState label="Пока нет данных Telegram за выбранный период. Включите сбор или алерты." />
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Collected</p>
                <p className="text-2xl font-semibold">{overview?.messages_collected ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Alerts sent</p>
                <p className="text-2xl font-semibold">{overview?.alerts_sent ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Suppressed</p>
                <p className="text-2xl font-semibold">{overview?.alerts_suppressed ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Channels</p>
                <p className="text-2xl font-semibold">{overview?.unique_channels ?? 0}</p>
              </div>
            </div>

            {health && (
              <div className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] text-xs text-[var(--text-muted)]">
                Health 24h: sent {health.alert_sent} · suppressed {health.alert_suppressed} ·
                digests {health.digests} · suppression {(health.suppression_rate * 100).toFixed(1)}%
              </div>
            )}

            {engagement && (
              <div className="space-y-4 pt-4 border-t border-[var(--border-color)]">
                <h4 className="text-sm font-semibold text-[var(--text-primary)]">Engagement (SMM)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)]">Total views</p>
                    <p className="text-2xl font-semibold">{engagement.total_views}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)]">Total likes</p>
                    <p className="text-2xl font-semibold">{engagement.total_likes}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)]">Published</p>
                    <p className="text-2xl font-semibold">{engagement.published_count}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                    <p className="text-xs text-[var(--text-muted)]">Avg ER</p>
                    <p className="text-2xl font-semibold">{Number(engagement.avg_er).toFixed(2)}%</p>
                  </div>
                </div>

                {engagement.top_posts.length > 0 ? (
                  <div>
                    <h5 className="text-sm font-semibold mb-2">Top posts by engagement</h5>
                    <ul className="space-y-2 text-sm">
                      {engagement.top_posts.map((post) => (
                        <li
                          key={post.id}
                          className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]"
                        >
                          <p className="text-[var(--text-primary)] line-clamp-2 mb-1">{post.post_text}</p>
                          <div className="flex flex-wrap gap-3 text-xs text-[var(--text-muted)]">
                            <span>Views {post.views}</span>
                            <span>Likes {post.likes}</span>
                            <span>Comments {post.comments}</span>
                            <span>Reposts {post.reposts}</span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <EmptyState label="Нет опубликованных постов с метриками за период." />
                )}
              </div>
            )}

            {sentiment && sentiment.total > 0 ? (
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <h4 className="text-sm font-semibold mb-2">Sentiment breakdown</h4>
                <p className="text-sm text-[var(--text-muted)]">
                  Positive: {sentiment.positive} · Negative: {sentiment.negative} · Neutral:{' '}
                  {sentiment.neutral}
                </p>
              </div>
            ) : (
              <EmptyState label="Sentiment пока пуст — включите AI-классификацию или batch enrichment." />
            )}

            {visibleChannels.length > 0 ? (
              <div>
                <h4 className="text-sm font-semibold mb-2">Top channels</h4>
                <ul className="space-y-1 text-sm">
                  {visibleChannels.map((ch) => (
                    <li key={ch.chat_id} className="flex justify-between">
                      <span>{ch.chat_id}</span>
                      <span>{ch.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <EmptyState label="Нет событий по каналам за период." />
            )}

            {keywords.length > 0 ? (
              <div>
                <h4 className="text-sm font-semibold mb-2">Top keywords</h4>
                <ul className="space-y-1 text-sm">
                  {keywords.map((kw) => (
                    <li key={kw.keyword} className="flex justify-between">
                      <span>{kw.keyword}</span>
                      <span>{kw.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <EmptyState label="Нет сработавших ключевых слов (alert_sent)." />
            )}

            {timeline.length > 0 ? (
              <div>
                <h4 className="text-sm font-semibold mb-2">Timeline (hourly)</h4>
                <ul className="space-y-1 text-xs text-[var(--text-muted)] max-h-48 overflow-y-auto">
                  {timeline.slice(-24).map((point) => (
                    <li key={point.bucket}>
                      {formatDateTime(point.bucket)}: collected {point.collected}, alerts{' '}
                      {point.alerts_sent}, suppressed {point.alerts_suppressed}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <EmptyState label="Timeline пуст за выбранный период." />
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
