import { FormEvent, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { ContentSeries, ContentSeriesCadence } from '@/types/smm'
import { DRAG_MIME, WEEKDAY_LABELS_MON, type DragPayload } from './calendar-utils'

const WEEKDAY_VALUES = [1, 2, 3, 4, 5, 6, 7] as const

interface SeriesPanelProps {
  series: ContentSeries[]
  maxSeries: number
  canCreate: boolean
  selectedSeriesId?: number
  onFilterSeries: (id: number | undefined) => void
  onCreate: (payload: {
    title: string
    color: string
    body: string
    weekdays: number[]
    publish_time: string
    cadence: ContentSeriesCadence
  }) => Promise<void>
  onToggleActive: (id: number, is_active: boolean) => Promise<void>
  onExpand: (id: number) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

export function SeriesPanel({
  series,
  maxSeries,
  canCreate,
  selectedSeriesId,
  onFilterSeries,
  onCreate,
  onToggleActive,
  onExpand,
  onDelete,
}: SeriesPanelProps) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [color, setColor] = useState('#8B5CF6')
  const [body, setBody] = useState('')
  const [publishTime, setPublishTime] = useState('10:00')
  const [cadence, setCadence] = useState<ContentSeriesCadence>('weekly')
  const [weekdays, setWeekdays] = useState<number[]>([1])
  const [busy, setBusy] = useState(false)

  const legend = useMemo(() => series.filter((s) => s.is_active), [series])

  function toggleWeekday(day: number) {
    setWeekdays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort(),
    )
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!title.trim() || !weekdays.length) return
    setBusy(true)
    try {
      await onCreate({
        title: title.trim(),
        color,
        body: body.trim() || title.trim(),
        weekdays,
        publish_time: publishTime,
        cadence,
      })
      setTitle('')
      setBody('')
      setOpen(false)
    } finally {
      setBusy(false)
    }
  }

  function onSeriesDragStart(e: React.DragEvent, s: ContentSeries) {
    const payload: DragPayload = { kind: 'series', seriesId: s.id }
    e.dataTransfer.setData(DRAG_MIME, JSON.stringify(payload))
    e.dataTransfer.effectAllowed = 'copy'
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base flex items-center justify-between gap-2">
          <span>Рубрики</span>
          <span className="text-xs font-normal text-[var(--text-muted)]">
            {series.length}/{maxSeries}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {legend.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={`text-xs rounded-full px-2 py-0.5 border ${
                selectedSeriesId == null
                  ? 'border-primary-400 text-primary-400'
                  : 'border-[var(--border-color)]'
              }`}
              onClick={() => onFilterSeries(undefined)}
            >
              All
            </button>
            {legend.map((s) => (
              <button
                key={s.id}
                type="button"
                className={`text-xs rounded-full px-2 py-0.5 border flex items-center gap-1 ${
                  selectedSeriesId === s.id
                    ? 'border-primary-400'
                    : 'border-[var(--border-color)]'
                }`}
                onClick={() =>
                  onFilterSeries(selectedSeriesId === s.id ? undefined : s.id)
                }
              >
                <span
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: s.color }}
                />
                {s.title}
              </button>
            ))}
          </div>
        )}

        {series.length === 0 && (
          <p className="text-xs text-[var(--text-muted)]">
            Создайте рубрику (повтор: дни недели + время). Перетащите на слот календаря.
          </p>
        )}

        <ul className="space-y-2">
          {series.map((s) => (
            <li
              key={s.id}
              draggable={s.is_active}
              onDragStart={(e) => onSeriesDragStart(e, s)}
              className={`rounded-md border border-[var(--border-color)] p-2 ${
                s.is_active ? 'cursor-grab' : 'opacity-60'
              }`}
              title="Drag onto calendar slot"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 font-medium truncate">
                    <span
                      className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: s.color }}
                    />
                    {s.title}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] mt-0.5">
                    {s.weekdays.map((d) => WEEKDAY_LABELS_MON[d - 1]).join(', ')} ·{' '}
                    {s.publish_time} · {s.cadence}
                  </div>
                </div>
                <div className="flex flex-col gap-0.5 shrink-0">
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 px-1 text-[10px]"
                    onClick={() => void onExpand(s.id)}
                  >
                    Expand
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 px-1 text-[10px]"
                    onClick={() => void onToggleActive(s.id, !s.is_active)}
                  >
                    {s.is_active ? 'Off' : 'On'}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 px-1 text-[10px] text-red-400"
                    onClick={() => void onDelete(s.id)}
                  >
                    Del
                  </Button>
                </div>
              </div>
            </li>
          ))}
        </ul>

        {!canCreate && (
          <p className="text-xs text-[var(--text-muted)]">
            Лимит рубрик исчерпан.{' '}
            <Link to="/pricing" className="text-primary-400 hover:underline">
              Upgrade
            </Link>
          </p>
        )}

        {canCreate && !open && (
          <Button size="sm" variant="secondary" onClick={() => setOpen(true)}>
            + Рубрика
          </Button>
        )}

        {open && (
          <form onSubmit={(e) => void submit(e)} className="space-y-2 border-t border-[var(--border-color)] pt-2">
            <Input
              placeholder="Название"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <textarea
              className="w-full min-h-[60px] rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1 text-sm"
              placeholder="Текст шаблона"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <div className="flex flex-wrap gap-1">
              {WEEKDAY_VALUES.map((d) => (
                <button
                  key={d}
                  type="button"
                  className={`text-[10px] px-1.5 py-0.5 rounded border ${
                    weekdays.includes(d)
                      ? 'border-primary-400 bg-primary-500/10'
                      : 'border-[var(--border-color)]'
                  }`}
                  onClick={() => toggleWeekday(d)}
                >
                  {WEEKDAY_LABELS_MON[d - 1]}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-2 items-center">
              <input
                type="time"
                value={publishTime}
                onChange={(e) => setPublishTime(e.target.value)}
                className="px-2 py-1 rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] text-sm"
              />
              <select
                value={cadence}
                onChange={(e) => setCadence(e.target.value as ContentSeriesCadence)}
                className="rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-2 py-1 text-sm"
              >
                <option value="weekly">Weekly</option>
                <option value="biweekly">Biweekly</option>
              </select>
              <input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="h-8 w-8 cursor-pointer"
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" type="submit" disabled={busy || !weekdays.length}>
                Create
              </Button>
              <Button size="sm" variant="ghost" type="button" onClick={() => setOpen(false)}>
                Cancel
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
