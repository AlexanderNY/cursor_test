import { FormEvent, useCallback, useEffect, useState } from 'react'
import {
  siteCreateHabit,
  siteDeleteHabit,
  siteListHabits,
  siteSetHabitCheck,
  type SiteUserHabit,
} from '@/data/site/site-api'
import { isoDate } from '@/components/tasks/task-utils'

function weekDays(today = new Date()): string[] {
  const start = new Date(today)
  start.setHours(12, 0, 0, 0)
  const weekday = (start.getDay() + 6) % 7
  start.setDate(start.getDate() - weekday)
  return Array.from({ length: 7 }, (_, index) => {
    const d = new Date(start)
    d.setDate(start.getDate() + index)
    return isoDate(d)
  })
}

export function HabitsPanel() {
  const [items, setItems] = useState<SiteUserHabit[]>([])
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const days = weekDays()
  const today = isoDate(new Date())

  const refresh = useCallback(async () => {
    try {
      setItems(await siteListHabits())
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить привычки')
      setItems([])
    } finally {
      setReady(true)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    const next = title.trim()
    if (!next || busy) {
      return
    }
    setBusy(true)
    try {
      await siteCreateHabit({ title: next })
      setTitle('')
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать')
    } finally {
      setBusy(false)
    }
  }

  async function toggle(habit: SiteUserHabit, day: string) {
    const checked = !habit.checks.includes(day)
    try {
      const updated = await siteSetHabitCheck(habit.id, { day, checked })
      setItems((prev) => prev.map((item) => (item.id === habit.id ? updated : item)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отметить')
    }
  }

  if (!ready) {
    return <p className="learn-section-note">Загрузка привычек…</p>
  }

  return (
    <section className="tasks-habits" aria-labelledby="tasks-habits-title">
      <header className="tasks-panel-head">
        <h2 id="tasks-habits-title" className="learn-section-title">
          Привычки
        </h2>
        <p className="learn-section-note">
          Отмечайте дни и копите серию. Неделя слева направо — пн–вс.
        </p>
      </header>

      <form className="tasks-habits-form" onSubmit={(event) => void handleCreate(event)}>
        <input
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Новая привычка…"
          maxLength={256}
          disabled={busy}
        />
        <button
          type="submit"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={busy || !title.trim()}
        >
          Добавить
        </button>
      </form>

      {error ? <p className="tasks-personal-error">{error}</p> : null}

      {items.length === 0 ? (
        <p className="learn-section-note">Пока нет привычек.</p>
      ) : (
        <ul className="tasks-habits-list">
          {items.map((habit) => (
            <li key={habit.id} className="tasks-habit-row">
              <div className="tasks-habit-info">
                <strong>{habit.title}</strong>
                <span className="tasks-mini-badge">серия {habit.streak}</span>
                {habit.tag ? <span className="tasks-mini-badge">{habit.tag}</span> : null}
              </div>
              <div className="tasks-habit-dots" role="group" aria-label={habit.title}>
                {days.map((day) => {
                  const on = habit.checks.includes(day)
                  return (
                    <button
                      key={day}
                      type="button"
                      className={[
                        'tasks-habit-dot',
                        on ? 'is-on' : '',
                        day === today ? 'is-today' : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      title={day}
                      aria-pressed={on}
                      onClick={() => void toggle(habit, day)}
                    />
                  )
                })}
              </div>
              <button
                type="button"
                className="learn-admin-link"
                onClick={() => {
                  if (!window.confirm(`Удалить «${habit.title}»?`)) {
                    return
                  }
                  void siteDeleteHabit(habit.id).then(refresh)
                }}
              >
                Удалить
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
