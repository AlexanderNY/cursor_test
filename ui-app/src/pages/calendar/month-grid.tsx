import type { BestTimeSlot, ContentSeries, PublishJob } from '@/types/smm'
import { JobChip } from './job-chip'
import {
  DRAG_MIME,
  WEEKDAY_LABELS_MON,
  isSameDay,
  jobDate,
  monthCellsMonFirst,
  parseDragPayload,
} from './calendar-utils'

interface MonthGridProps {
  cursor: Date
  jobs: PublishJob[]
  seriesById: Map<number, ContentSeries>
  brandColor: (brandId?: number | null) => string
  maxScheduleDate: Date
  horizonDays: number
  bestSlots?: BestTimeSlot[]
  onDropJob: (jobId: number, day: Date, hour?: number) => void
  onDropSeries: (seriesId: number, day: Date, hour?: number) => void
  onEmptyClick?: (day: Date) => void
  readOnly?: boolean
}

export function MonthGrid({
  cursor,
  jobs,
  seriesById,
  brandColor,
  maxScheduleDate,
  horizonDays,
  onDropJob,
  onDropSeries,
  onEmptyClick,
  readOnly = false,
}: MonthGridProps) {
  const cells = monthCellsMonFirst(cursor.getFullYear(), cursor.getMonth())
  const MAX_VISIBLE = 3

  function jobsForDay(day: number): PublishJob[] {
    return jobs.filter((j) => {
      const d = jobDate(j)
      if (!d) return false
      return (
        d.getFullYear() === cursor.getFullYear() &&
        d.getMonth() === cursor.getMonth() &&
        d.getDate() === day
      )
    })
  }

  function handleDrop(e: React.DragEvent, dayDate: Date, beyond: boolean) {
    e.preventDefault()
    if (beyond || readOnly) return
    const payload = parseDragPayload(e.dataTransfer.getData(DRAG_MIME))
    if (!payload) return
    if (payload.kind === 'job') onDropJob(payload.jobId, dayDate)
    else onDropSeries(payload.seriesId, dayDate)
  }

  return (
    <div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-[var(--text-muted)] mb-2">
        {WEEKDAY_LABELS_MON.map((w) => (
          <div key={w}>{w}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((day, idx) => {
          const dayDate =
            day != null
              ? new Date(cursor.getFullYear(), cursor.getMonth(), day, 12, 0, 0)
              : null
          const beyond = dayDate != null && dayDate > maxScheduleDate
          const dayJobs = day != null ? jobsForDay(day) : []
          const overflow = dayJobs.length - MAX_VISIBLE
          return (
            <div
              key={idx}
              className={`min-h-[96px] rounded-md border border-[var(--border-color)] p-1 ${
                beyond ? 'opacity-40 bg-[var(--bg-secondary)]' : ''
              }`}
              title={beyond ? `Outside schedule horizon (${horizonDays} days)` : undefined}
              onDragOver={(e) => {
                if (!beyond && !readOnly && day != null) e.preventDefault()
              }}
              onDrop={(e) => {
                if (dayDate) handleDrop(e, dayDate, beyond)
              }}
              onDoubleClick={() => {
                if (dayDate && !beyond && !readOnly) onEmptyClick?.(dayDate)
              }}
            >
              {day != null && (
                <>
                  <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-1">
                    <span>{day}</span>
                    {dayJobs.length > 0 && (
                      <span className="rounded-full bg-[var(--bg-secondary)] px-1.5 text-[10px]">
                        {dayJobs.length}
                      </span>
                    )}
                  </div>
                  {dayJobs.slice(0, MAX_VISIBLE).map((j) => {
                    const series = j.series_id != null ? seriesById.get(j.series_id) : undefined
                    const color = series?.color ?? brandColor(j.brand_id)
                    return (
                      <JobChip
                        key={j.id}
                        job={j}
                        color={color}
                        series={series}
                        draggable={!beyond && !readOnly}
                      />
                    )
                  })}
                  {overflow > 0 && (
                    <div className="text-[10px] text-[var(--text-muted)]">+{overflow}</div>
                  )}
                </>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** Highlight helper unused in month but kept for week best-times. */
export function isBestSlot(
  slots: BestTimeSlot[] | undefined,
  day: Date,
  hour: number,
): boolean {
  if (!slots?.length) return false
  // BestTimeSlot.weekday: 0=Sun … 6=Sat (matches existing Best times UI)
  const wd = day.getDay()
  return slots.some((s) => s.weekday === wd && s.hour === hour)
}

export function jobsOnDay(jobs: PublishJob[], day: Date): PublishJob[] {
  return jobs.filter((j) => {
    const d = jobDate(j)
    return d != null && isSameDay(d, day)
  })
}
