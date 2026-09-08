import type { BestTimeSlot, ContentSeries, PublishJob } from '@/types/smm'
import { JobChip } from './job-chip'
import {
  DRAG_MIME,
  WEEKDAY_LABELS_MON,
  WORK_HOURS,
  isSameDay,
  jobDate,
  parseDragPayload,
} from './calendar-utils'
import { isBestSlot } from './month-grid'

interface WeekGridProps {
  weekStart: Date
  jobs: PublishJob[]
  seriesById: Map<number, ContentSeries>
  brandColor: (brandId?: number | null) => string
  maxScheduleDate: Date
  horizonDays: number
  bestSlots?: BestTimeSlot[]
  onDropJob: (jobId: number, day: Date, hour?: number) => void
  onDropSeries: (seriesId: number, day: Date, hour?: number) => void
  onEmptyClick?: (day: Date, hour: number) => void
  readOnly?: boolean
}

export function WeekGrid({
  weekStart,
  jobs,
  seriesById,
  brandColor,
  maxScheduleDate,
  horizonDays,
  bestSlots,
  onDropJob,
  onDropSeries,
  onEmptyClick,
  readOnly = false,
}: WeekGridProps) {
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart)
    d.setDate(d.getDate() + i)
    return d
  })

  function handleDrop(e: React.DragEvent, day: Date, hour: number, beyond: boolean) {
    e.preventDefault()
    if (beyond || readOnly) return
    const payload = parseDragPayload(e.dataTransfer.getData(DRAG_MIME))
    if (!payload) return
    if (payload.kind === 'job') onDropJob(payload.jobId, day, hour)
    else onDropSeries(payload.seriesId, day, hour)
  }

  function jobsInSlot(day: Date, hour: number): PublishJob[] {
    return jobs.filter((j) => {
      const d = jobDate(j)
      if (!d || !isSameDay(d, day)) return false
      return d.getHours() === hour
    })
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[720px]">
        <div className="grid grid-cols-[48px_repeat(7,1fr)] gap-1 text-center text-xs text-[var(--text-muted)] mb-1">
          <div />
          {days.map((d, i) => (
            <div key={i}>
              <div>{WEEKDAY_LABELS_MON[i]}</div>
              <div className="font-medium text-[var(--text-primary)]">{d.getDate()}</div>
            </div>
          ))}
        </div>
        {WORK_HOURS.map((hour) => (
          <div key={hour} className="grid grid-cols-[48px_repeat(7,1fr)] gap-1 mb-1">
            <div className="text-[10px] text-[var(--text-muted)] pt-1 text-right pr-1">
              {String(hour).padStart(2, '0')}:00
            </div>
            {days.map((day, di) => {
              const slotDate = new Date(
                day.getFullYear(),
                day.getMonth(),
                day.getDate(),
                hour,
                0,
                0,
              )
              const beyond = slotDate > maxScheduleDate
              const slotJobs = jobsInSlot(day, hour)
              const highlight = !beyond && isBestSlot(bestSlots, day, hour)
              return (
                <div
                  key={di}
                  className={`min-h-[40px] rounded border border-[var(--border-color)] p-0.5 ${
                    beyond ? 'opacity-40 bg-[var(--bg-secondary)]' : ''
                  } ${highlight ? 'ring-1 ring-emerald-400/60 bg-emerald-500/5' : ''}`}
                  title={
                    beyond
                      ? `Outside schedule horizon (${horizonDays} days)`
                      : highlight
                        ? 'Best time'
                        : undefined
                  }
                  onDragOver={(e) => {
                    if (!beyond && !readOnly) e.preventDefault()
                  }}
                  onDrop={(e) => handleDrop(e, day, hour, beyond)}
                  onDoubleClick={() => {
                    if (!beyond && !readOnly) onEmptyClick?.(day, hour)
                  }}
                >
                  {slotJobs.map((j) => {
                    const series = j.series_id != null ? seriesById.get(j.series_id) : undefined
                    const color = series?.color ?? brandColor(j.brand_id)
                    return (
                      <JobChip
                        key={j.id}
                        job={j}
                        color={color}
                        series={series}
                        compact
                        draggable={!beyond && !readOnly}
                      />
                    )
                  })}
                </div>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
