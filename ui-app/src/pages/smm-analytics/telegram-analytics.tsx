import { useEffect, useMemo, useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { telegramService } from '@/services/telegram-service'
import type {
  TgAnalyticsOverview,
  TgAnalyticsChannelItem,
  TgAnalyticsKeywordItem,
  TgAnalyticsTimelinePoint,
  TgAnalyticsSentimentBreakdown,
  TgAnalyticsEngagement,
} from '@/types/telegram'
import { formatDateTime } from '@/utils/date'

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

export function TelegramAnalyticsPanel({
  chatIdFilter = null,
}: {
  chatIdFilter?: string | null
}) {
  const [isLoading, setIsLoading] = useState(true)
  const [overview, setOverview] = useState<TgAnalyticsOverview | null>(null)
  const [channels, setChannels] = useState<TgAnalyticsChannelItem[]>([])
  const [keywords, setKeywords] = useState<TgAnalyticsKeywordItem[]>([])
  const [timeline, setTimeline] = useState<TgAnalyticsTimelinePoint[]>([])
  const [sentiment, setSentiment] = useState<TgAnalyticsSentimentBreakdown | null>(null)
  const [engagement, setEngagement] = useState<TgAnalyticsEngagement | null>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      setIsLoading(true)
      try {
        const [ov, ch, kw, tl, sent, eng] = await Promise.all([
          telegramService.getAnalyticsOverview('7d'),
          telegramService.getAnalyticsChannels('7d', 10),
          telegramService.getAnalyticsKeywords('7d', 20),
          telegramService.getAnalyticsTimeline('7d', 'hour'),
          telegramService.getAnalyticsSentiment('7d'),
          telegramService.getAnalyticsEngagement('7d', 10),
        ])
        if (cancelled) return
        setOverview(ov)
        setChannels(ch)
        setKeywords(kw)
        setTimeline(tl)
        setSentiment(sent)
        setEngagement(eng)
      } catch (err) {
        console.warn('Telegram analytics load failed', err)
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const visibleChannels = useMemo(() => {
    if (!chatIdFilter) return channels
    return channels.filter((c) => sameChatId(c.chat_id, chatIdFilter))
  }, [channels, chatIdFilter])

  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Telegram Analytics</CardTitle>
        <CardDescription>Метрики сбора и engagement за последние 7 дней</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading analytics...</div>
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
                    <p className="text-2xl font-semibold">{(engagement.avg_er * 100).toFixed(2)}%</p>
                  </div>
                </div>

                {engagement.top_posts.length > 0 && (
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
                            <span>👁 {post.views}</span>
                            <span>❤ {post.likes}</span>
                            <span>💬 {post.comments}</span>
                            <span>↗ {post.reposts}</span>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {sentiment && sentiment.total > 0 && (
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <h4 className="text-sm font-semibold mb-2">Sentiment breakdown</h4>
                <p className="text-sm text-[var(--text-muted)]">
                  Positive: {sentiment.positive} · Negative: {sentiment.negative} · Neutral:{' '}
                  {sentiment.neutral}
                </p>
              </div>
            )}

            {visibleChannels.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">
                  Top channels
                  {chatIdFilter ? ` · filter ${chatIdFilter}` : ''}
                </h4>
                <ul className="space-y-1 text-sm">
                  {visibleChannels.map((ch) => (
                    <li key={ch.chat_id} className="flex justify-between">
                      <span>{ch.chat_id}</span>
                      <span>{ch.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {keywords.length > 0 && (
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
            )}

            {timeline.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Timeline (hourly)</h4>
                <ul className="space-y-1 text-xs text-[var(--text-muted)] max-h-48 overflow-y-auto">
                  {timeline.slice(-24).map((point) => (
                    <li key={point.bucket}>
                      {formatDateTime(point.bucket)}: collected {point.collected}, alerts {point.alerts_sent},
                      suppressed {point.alerts_suppressed}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
