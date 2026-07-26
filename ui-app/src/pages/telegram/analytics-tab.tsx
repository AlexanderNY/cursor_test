import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import type {
  TgAnalyticsOverview,
  TgAnalyticsChannelItem,
  TgAnalyticsKeywordItem,
  TgAnalyticsTimelinePoint,
  TgAnalyticsSentimentBreakdown,
  TgAnalyticsEngagement,
} from '@/types/telegram'

export interface AnalyticsTabProps {
  isLoadingAnalytics: boolean
  analyticsOverview: TgAnalyticsOverview | null
  analyticsChannels: TgAnalyticsChannelItem[]
  analyticsKeywords: TgAnalyticsKeywordItem[]
  analyticsTimeline: TgAnalyticsTimelinePoint[]
  analyticsSentiment: TgAnalyticsSentimentBreakdown | null
  engagement: TgAnalyticsEngagement | null
}

export function AnalyticsTab({
  isLoadingAnalytics,
  analyticsOverview,
  analyticsChannels,
  analyticsKeywords,
  analyticsTimeline,
  analyticsSentiment,
  engagement,
}: AnalyticsTabProps) {
  return (
    <Card className="animate-slide-up">
      <CardHeader>
        <CardTitle>Telegram Analytics</CardTitle>
        <CardDescription>Метрики за последние 7 дней</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoadingAnalytics ? (
          <div className="text-center py-8 text-[var(--text-muted)]">Loading analytics...</div>
        ) : (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Collected</p>
                <p className="text-2xl font-semibold">{analyticsOverview?.messages_collected ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Alerts sent</p>
                <p className="text-2xl font-semibold">{analyticsOverview?.alerts_sent ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Suppressed</p>
                <p className="text-2xl font-semibold">{analyticsOverview?.alerts_suppressed ?? 0}</p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <p className="text-xs text-[var(--text-muted)]">Channels</p>
                <p className="text-2xl font-semibold">{analyticsOverview?.unique_channels ?? 0}</p>
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
                        <li key={post.id} className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)]">
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

            {analyticsSentiment && analyticsSentiment.total > 0 && (
              <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]">
                <h4 className="text-sm font-semibold mb-2">Sentiment breakdown</h4>
                <p className="text-sm text-[var(--text-muted)]">
                  Positive: {analyticsSentiment.positive} · Negative: {analyticsSentiment.negative} · Neutral: {analyticsSentiment.neutral}
                </p>
              </div>
            )}

            {analyticsChannels.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Top channels</h4>
                <ul className="space-y-1 text-sm">
                  {analyticsChannels.map((ch) => (
                    <li key={ch.chat_id} className="flex justify-between">
                      <span>{ch.chat_id}</span>
                      <span>{ch.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {analyticsKeywords.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Top keywords</h4>
                <ul className="space-y-1 text-sm">
                  {analyticsKeywords.map((kw) => (
                    <li key={kw.keyword} className="flex justify-between">
                      <span>{kw.keyword}</span>
                      <span>{kw.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {analyticsTimeline.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Timeline (hourly)</h4>
                <ul className="space-y-1 text-xs text-[var(--text-muted)] max-h-48 overflow-y-auto">
                  {analyticsTimeline.slice(-24).map((point) => (
                    <li key={point.bucket}>
                      {point.bucket}: collected {point.collected}, alerts {point.alerts_sent}, suppressed {point.alerts_suppressed}
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
