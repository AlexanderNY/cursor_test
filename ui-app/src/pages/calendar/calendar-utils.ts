import type { ContentSeries, PublishJob } from '@/types/smm'

export const WEEKDAY_LABELS_MON = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const

export const WORK_HOURS = Array.from({ length: 15 }, (_, i) => i + 8) // 08–22

export type CalendarView = 'week' | 'month'

export type DragPayload =
  | { kind: 'job'; jobId: number }
  | { kind: 'series'; seriesId: number }

export function getMondayWeekStart(date: Date): Date {
  const d = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const day = d.getDay() // 0=Sun
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

export function formatWeekLabel(weekStart: Date): string {
  const end = new Date(weekStart)
  end.setDate(end.getDate() + 6)
  const opts: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }
  return `${weekStart.toLocaleDateString(undefined, opts)} – ${end.toLocaleDateString(undefined, {
    ...opts,
    year: 'numeric',
  })}`
}

export function statusBadge(status: string): string {
  if (status === 'pending_approval') return '⏳ '
  if (status === 'rejected') return '✕ '
  if (status === 'failed') return '! '
  if (status === 'published') return '✓ '
  return ''
}

export function isJobLocked(status: string): boolean {
  return status === 'published' || status === 'publishing'
}

export function jobDate(job: PublishJob): Date | null {
  const iso = job.publish_at || job.created_at
  if (!iso) return null
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? null : d
}

export function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

/** Month cells Mon-first: null padding then day numbers. */
export function monthCellsMonFirst(year: number, month: number): (number | null)[] {
  const count = new Date(year, month + 1, 0).getDate()
  const firstDow = new Date(year, month, 1).getDay() // 0=Sun
  const startPad = firstDow === 0 ? 6 : firstDow - 1
  const cells: (number | null)[] = []
  for (let i = 0; i < startPad; i++) cells.push(null)
  for (let d = 1; d <= count; d++) cells.push(d)
  while (cells.length % 7 !== 0) cells.push(null)
  return cells
}

export function seriesColorMap(series: ContentSeries[]): Map<number, string> {
  const m = new Map<number, string>()
  for (const s of series) m.set(s.id, s.color || '#8B5CF6')
  return m
}

export function parseDragPayload(raw: string): DragPayload | null {
  try {
    const data = JSON.parse(raw) as DragPayload
    if (data?.kind === 'job' && typeof data.jobId === 'number') return data
    if (data?.kind === 'series' && typeof data.seriesId === 'number') return data
  } catch {
    /* ignore */
  }
  return null
}

export const DRAG_MIME = 'application/x-smm-calendar'
