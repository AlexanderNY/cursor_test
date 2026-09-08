import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Alert } from '@/components/ui/alert'
import { smmService } from '@/services/smm-service'
import type { AnalyticsPost, AnalyticsPostDetail } from '@/types/smm'
import { formatDateTime } from '@/utils/date'
import { getErrorMessage } from '@/services/api-client'
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'

export function PostDetailDrawer({
  post,
  onClose,
}: {
  post: AnalyticsPost | null
  onClose: () => void
}) {
  const [detail, setDetail] = useState<AnalyticsPostDetail | null>(null)
  const [error, setError] = useState('')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    if (!post) {
      setDetail(null)
      return
    }
    let cancelled = false
    void (async () => {
      setError('')
      try {
        const data = await smmService.analyticsPostDetail(post.network, post.id)
        if (!cancelled) setDetail(data)
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err))
      }
    })()
    return () => {
      cancelled = true
    }
  }, [post])

  if (!post) return null

  async function handleRefresh() {
    if (!post) return
    setRefreshing(true)
    setError('')
    try {
      const res = await smmService.analyticsPostRefresh(post.network, post.id)
      if (!res.ok) setError(res.error || 'Не удалось обновить')
      const data = await smmService.analyticsPostDetail(post.network, post.id)
      setDetail(data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setRefreshing(false)
    }
  }

  const series = (detail?.series || []).map((s) => ({
    ...s,
    t: s.captured_at ? formatDateTime(s.captured_at) : '',
  }))

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40" onClick={onClose}>
      <aside
        className="w-full max-w-lg h-full bg-[var(--bg-primary)] border-l border-[var(--border-color)] shadow-xl overflow-y-auto p-4 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-2">
          <div>
            <h3 className="text-lg font-semibold">Пост · {post.network.toUpperCase()}</h3>
            <p className="text-sm text-[var(--text-muted)]">
              {detail?.channel_title || post.channel_title || '—'}
            </p>
          </div>
          <Button variant="secondary" onClick={onClose}>
            Закрыть
          </Button>
        </div>
        {error && <Alert variant="error">{error}</Alert>}
        <p className="text-sm whitespace-pre-wrap">{detail?.text || post.text}</p>
        <div className="grid grid-cols-4 gap-2 text-center text-sm">
          {[
            ['Views', detail?.views ?? post.views],
            ['Likes', detail?.likes ?? post.likes],
            ['Comments', detail?.comments ?? post.comments],
            ['ER', `${detail?.er ?? post.er}%`],
          ].map(([k, v]) => (
            <div key={String(k)} className="rounded-lg border border-[var(--border-color)] p-2">
              <p className="text-xs text-[var(--text-muted)]">{k}</p>
              <p className="font-semibold">{v}</p>
            </div>
          ))}
        </div>
        <Button onClick={() => void handleRefresh()} disabled={refreshing}>
          {refreshing ? 'Обновление…' : 'Обновить метрики'}
        </Button>
        <div>
          <h4 className="text-sm font-semibold mb-2">История метрик</h4>
          {series.length > 0 ? (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="t" hide />
                  <YAxis tick={{ fontSize: 10 }} width={36} />
                  <Tooltip />
                  <Line type="monotone" dataKey="views" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-[var(--text-muted)]">Snapshots ещё нет — нажмите «Обновить метрики».</p>
          )}
        </div>
        <div>
          <h4 className="text-sm font-semibold mb-2">Комментарии (inbox)</h4>
          <ul className="space-y-2">
            {(detail?.inbox_comments || []).map((c) => (
              <li key={c.id} className="rounded-lg border border-[var(--border-color)] p-2 text-sm">
                <div className="flex justify-between text-xs text-[var(--text-muted)] mb-1">
                  <span>{c.author || 'anon'}</span>
                  <span>{c.created_at ? formatDateTime(c.created_at) : ''} · {c.status}</span>
                </div>
                <p>{c.text || '—'}</p>
              </li>
            ))}
            {(detail?.inbox_comments || []).length === 0 && (
              <p className="text-sm text-[var(--text-muted)]">Нет связанных комментариев</p>
            )}
          </ul>
        </div>
      </aside>
    </div>
  )
}
