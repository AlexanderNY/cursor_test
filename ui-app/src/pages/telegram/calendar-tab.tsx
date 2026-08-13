import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { SkeletonCard } from '@/components/ui/skeleton'
import type { TelegramPostListItem } from '@/types/telegram'
import { formatWeekLabel, getWeekStart, toDatetimeLocalValue, fromDatetimeLocalValue } from './telegram-helpers'
import { formatDateTime } from '@/utils/date'

export interface CalendarTabProps {
  posts: TelegramPostListItem[]
  weekStart: Date
  isLoading: boolean
  onWeekChange: (weekStart: Date) => void
  onReschedule: (postId: number, newIsoDatetime: string) => Promise<void>
}

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function getPostDate(post: TelegramPostListItem): Date {
  const raw = post.publish_at || post.created_at
  return new Date(raw)
}

function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

export function CalendarTab({
  posts,
  weekStart,
  isLoading,
  onWeekChange,
  onReschedule,
}: CalendarTabProps) {
  const [reschedulePostId, setReschedulePostId] = useState<number | null>(null)
  const [rescheduleValue, setRescheduleValue] = useState('')
  const [isRescheduling, setIsRescheduling] = useState(false)

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + i)
    return d
  })

  function goPrevWeek() {
    const prev = new Date(weekStart)
    prev.setDate(prev.getDate() - 7)
    onWeekChange(getWeekStart(prev))
  }

  function goNextWeek() {
    const next = new Date(weekStart)
    next.setDate(next.getDate() + 7)
    onWeekChange(getWeekStart(next))
  }

  function goThisWeek() {
    onWeekChange(getWeekStart(new Date()))
  }

  function openReschedule(post: TelegramPostListItem) {
    if (post.id == null) return
    setReschedulePostId(post.id)
    setRescheduleValue(toDatetimeLocalValue(post.publish_at || post.created_at))
  }

  async function submitReschedule() {
    if (reschedulePostId == null) return
    const iso = fromDatetimeLocalValue(rescheduleValue)
    if (!iso) return
    setIsRescheduling(true)
    try {
      await onReschedule(reschedulePostId, iso)
      setReschedulePostId(null)
      setRescheduleValue('')
    } finally {
      setIsRescheduling(false)
    }
  }

  return (
    <Card className="animate-slide-up">
      <CardHeader className="flex flex-row items-center justify-between gap-2 flex-wrap">
        <div>
          <CardTitle className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Calendar
          </CardTitle>
          <CardDescription>
            Week view — click a post to reschedule.{' '}
            <a href="/calendar?network=tg" className="text-primary-400 hover:underline">
              Open shared calendar →
            </a>
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={goPrevWeek}>← Prev</Button>
          <Button type="button" variant="secondary" size="sm" onClick={goThisWeek}>Today</Button>
          <Button type="button" variant="ghost" size="sm" onClick={goNextWeek}>Next →</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm font-medium text-[var(--text-secondary)]">{formatWeekLabel(weekStart)}</p>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
            {days.map((day, idx) => {
              const dayPosts = posts.filter((p) => isSameDay(getPostDate(p), day))
              return (
                <div
                  key={day.toISOString()}
                  className="min-h-[120px] p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-color)]"
                >
                  <div className="text-xs font-semibold text-[var(--text-muted)] mb-2">
                    {DAY_NAMES[idx]} {day.getDate()}
                  </div>
                  <div className="space-y-2">
                    {dayPosts.length === 0 && (
                      <p className="text-xs text-[var(--text-muted)]">—</p>
                    )}
                    {dayPosts.map((post) => (
                      <button
                        key={post.id}
                        type="button"
                        onClick={() => openReschedule(post)}
                        className="w-full text-left p-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-primary-500/10 border border-[var(--border-color)] transition-colors"
                      >
                        <p className="text-xs text-[var(--text-primary)] line-clamp-2">{post.post_text}</p>
                        <div className="flex items-center gap-1 mt-1 flex-wrap">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[var(--text-muted)]">
                            {post.status}
                          </span>
                          {post.publish_at && (
                            <span className="text-[10px] text-primary-400">
                              {formatDateTime(post.publish_at)}
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {reschedulePostId != null && (
          <div className="p-4 rounded-xl border border-primary-500/30 bg-primary-500/5 space-y-3">
            <h4 className="text-sm font-medium text-[var(--text-primary)]">Reschedule post</h4>
            <input
              type="datetime-local"
              value={rescheduleValue}
              onChange={(e) => setRescheduleValue(e.target.value)}
              className="w-full max-w-xs px-4 py-2.5 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
            <div className="flex gap-2">
              <Button type="button" size="sm" onClick={submitReschedule} isLoading={isRescheduling}>
                Save
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => setReschedulePostId(null)}>
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
