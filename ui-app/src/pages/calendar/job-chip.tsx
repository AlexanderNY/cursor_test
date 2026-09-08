import { Link } from 'react-router-dom'
import type { ContentSeries, PublishJob } from '@/types/smm'
import { DRAG_MIME, isJobLocked, statusBadge, type DragPayload } from './calendar-utils'

interface JobChipProps {
  job: PublishJob
  color: string
  series?: ContentSeries | null
  draggable?: boolean
  compact?: boolean
}

export function JobChip({
  job,
  color,
  series,
  draggable = true,
  compact = false,
}: JobChipProps) {
  const locked = isJobLocked(job.status)
  const canDrag = draggable && !locked
  const label = job.source_text.slice(0, compact ? 28 : 40)
  const time =
    job.publish_at != null
      ? new Date(job.publish_at).toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
        })
      : null

  function handleDragStart(e: React.DragEvent) {
    if (!canDrag) {
      e.preventDefault()
      return
    }
    const payload: DragPayload = { kind: 'job', jobId: job.id }
    e.dataTransfer.setData(DRAG_MIME, JSON.stringify(payload))
    e.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div
      draggable={canDrag}
      onDragStart={handleDragStart}
      className={`text-[10px] truncate rounded px-1 py-0.5 mb-0.5 text-white ${
        canDrag ? 'cursor-grab active:cursor-grabbing' : 'opacity-90'
      }`}
      style={{ backgroundColor: color }}
      title={`${job.status}${series ? ` · ${series.title}` : ''}: ${job.source_text}`}
    >
      <Link
        to={`/posts?job=${job.id}`}
        className="text-white hover:underline"
        onClick={(e) => e.stopPropagation()}
        draggable={false}
      >
        {statusBadge(job.status)}
        {!compact && time ? `${time} ` : ''}
        {label}
      </Link>
    </div>
  )
}
