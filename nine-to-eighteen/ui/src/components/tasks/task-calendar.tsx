import { useMemo, useState } from 'react'
import type { SiteUserTask } from '@/data/site/site-api'
import { TaskCard } from '@/components/tasks/task-card'
import { isoDate, startOfWeek } from '@/components/tasks/task-utils'

type CalMode = 'day' | 'week' | 'month'

type TaskCalendarProps = {
  items: SiteUserTask[]
  onToggle: (task: SiteUserTask) => void
  onOpen: (task: SiteUserTask) => void
  onPickDay: (iso: string) => void
}

function tasksOnDay(items: SiteUserTask[], day: string): SiteUserTask[] {
  return items.filter((task) => task.dueAt === day)
}

export function TaskCalendar({
  items,
  onToggle,
  onOpen,
  onPickDay,
}: TaskCalendarProps) {
  const [mode, setMode] = useState<CalMode>('week')
  const [anchor, setAnchor] = useState(() => {
    const d = new Date()
    d.setHours(12, 0, 0, 0)
    return d
  })

  const days = useMemo(() => {
    if (mode === 'day') {
      return [new Date(anchor)]
    }
    if (mode === 'week') {
      const start = startOfWeek(anchor)
      return Array.from({ length: 7 }, (_, index) => {
        const d = new Date(start)
        d.setDate(start.getDate() + index)
        return d
      })
    }
    const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1)
    const start = startOfWeek(first)
    return Array.from({ length: 42 }, (_, index) => {
      const d = new Date(start)
      d.setDate(start.getDate() + index)
      return d
    })
  }, [anchor, mode])

  const title = useMemo(() => {
    if (mode === 'day') {
      return anchor.toLocaleDateString('ru-RU', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      })
    }
    if (mode === 'week') {
      const start = days[0]
      const end = days[days.length - 1]
      return `${start.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })} – ${end.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })}`
    }
    return anchor.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })
  }, [anchor, days, mode])

  function shift(delta: number) {
    setAnchor((prev) => {
      const next = new Date(prev)
      if (mode === 'day') {
        next.setDate(next.getDate() + delta)
      } else if (mode === 'week') {
        next.setDate(next.getDate() + delta * 7)
      } else {
        next.setMonth(next.getMonth() + delta)
      }
      return next
    })
  }

  const todayIso = isoDate(new Date())

  return (
    <div className="tasks-calendar">
      <div className="tasks-calendar-toolbar">
        <div className="tasks-view-tabs" role="tablist" aria-label="Масштаб календаря">
          {(
            [
              ['day', 'День'],
              ['week', 'Неделя'],
              ['month', 'Месяц'],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={mode === id}
              className={mode === id ? 'tasks-view-tab is-active' : 'tasks-view-tab'}
              onClick={() => setMode(id)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="tasks-calendar-nav">
          <button type="button" className="learn-admin-btn" onClick={() => shift(-1)}>
            ←
          </button>
          <button
            type="button"
            className="learn-admin-btn"
            onClick={() => {
              const d = new Date()
              d.setHours(12, 0, 0, 0)
              setAnchor(d)
            }}
          >
            Сегодня
          </button>
          <button type="button" className="learn-admin-btn" onClick={() => shift(1)}>
            →
          </button>
          <span className="tasks-calendar-title">{title}</span>
        </div>
      </div>

      <div
        className={
          mode === 'month'
            ? 'tasks-calendar-grid is-month'
            : mode === 'day'
              ? 'tasks-calendar-grid is-day'
              : 'tasks-calendar-grid is-week'
        }
      >
        {days.map((day) => {
          const key = isoDate(day)
          const dayTasks = tasksOnDay(items, key)
          const outsideMonth =
            mode === 'month' && day.getMonth() !== anchor.getMonth()
          return (
            <div
              key={key}
              className={[
                'tasks-cal-cell',
                key === todayIso ? 'is-today' : '',
                outsideMonth ? 'is-outside' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <button
                type="button"
                className="tasks-cal-daybtn"
                onClick={() => onPickDay(key)}
                title="Создать задачу на этот день"
              >
                <span className="tasks-cal-weekday">
                  {day.toLocaleDateString('ru-RU', { weekday: 'short' })}
                </span>
                <span className="tasks-cal-num">{day.getDate()}</span>
              </button>
              <div className="tasks-cal-items">
                {dayTasks.slice(0, mode === 'month' ? 3 : 8).map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    compact
                    onToggle={onToggle}
                    onOpen={onOpen}
                  />
                ))}
                {dayTasks.length > (mode === 'month' ? 3 : 8) ? (
                  <span className="tasks-cal-more">
                    ещё {dayTasks.length - (mode === 'month' ? 3 : 8)}
                  </span>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
