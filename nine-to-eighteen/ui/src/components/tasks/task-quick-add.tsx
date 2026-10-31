import { FormEvent, useEffect, useState } from 'react'
import type {
  SiteTaskBoard,
  SiteTaskPriority,
  SiteTaskRepeat,
} from '@/data/site/site-api'
import { TAG_PRESETS } from '@/components/tasks/task-utils'

const PREFS_KEY = '9to18-tasks-quick-prefs'

type Prefs = {
  tag: string
  priority: SiteTaskPriority
  board: SiteTaskBoard
  dueAt: string
  dueTime: string
  repeatRule: SiteTaskRepeat
}

const DEFAULT_PREFS: Prefs = {
  tag: '',
  priority: 'normal',
  board: 'backlog',
  dueAt: '',
  dueTime: '',
  repeatRule: 'none',
}

function loadPrefs(): Prefs {
  try {
    const raw = sessionStorage.getItem(PREFS_KEY)
    if (!raw) {
      return DEFAULT_PREFS
    }
    return { ...DEFAULT_PREFS, ...(JSON.parse(raw) as Partial<Prefs>) }
  } catch {
    return DEFAULT_PREFS
  }
}

type TaskQuickAddProps = {
  busy?: boolean
  defaultDueAt?: string
  onCreate: (input: {
    title: string
    tag: string
    priority: SiteTaskPriority
    board: SiteTaskBoard
    due_at: string | null
    due_time: string | null
    repeat_rule: SiteTaskRepeat
  }) => Promise<void>
}

export function TaskQuickAdd({ busy, defaultDueAt, onCreate }: TaskQuickAddProps) {
  const [title, setTitle] = useState('')
  const [prefs, setPrefs] = useState<Prefs>(() => loadPrefs())
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (defaultDueAt) {
      setPrefs((prev) => ({ ...prev, dueAt: defaultDueAt }))
    }
  }, [defaultDueAt])

  useEffect(() => {
    sessionStorage.setItem(PREFS_KEY, JSON.stringify(prefs))
  }, [prefs])

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nextTitle = title.trim()
    if (!nextTitle || busy) {
      return
    }
    await onCreate({
      title: nextTitle,
      tag: prefs.tag.trim(),
      priority: prefs.priority,
      board: prefs.board,
      due_at: prefs.dueAt.trim() || null,
      due_time: prefs.dueTime.trim() || null,
      repeat_rule: prefs.repeatRule,
    })
    setTitle('')
  }

  return (
    <form className="tasks-quick-add" onSubmit={(event) => void handleSubmit(event)}>
      <div className="tasks-quick-row">
        <input
          className="tasks-quick-input"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Быстрая задача… Enter"
          maxLength={512}
          disabled={busy}
          aria-label="Новая задача"
        />
        <button
          type="submit"
          className="learn-admin-btn learn-admin-btn-primary"
          disabled={busy || !title.trim()}
        >
          {busy ? '…' : 'Добавить'}
        </button>
        <button
          type="button"
          className="learn-admin-btn"
          onClick={() => setExpanded((value) => !value)}
          aria-expanded={expanded}
        >
          {expanded ? 'Скрыть' : 'Параметры'}
        </button>
      </div>

      {expanded ? (
        <div className="tasks-quick-chips" aria-label="Параметры новой задачи">
          <div className="tasks-chip-group">
            <span className="tasks-chip-label">Метка</span>
            {TAG_PRESETS.map((preset) => (
              <button
                key={preset}
                type="button"
                className={
                  prefs.tag === preset ? 'tasks-chip is-active' : 'tasks-chip'
                }
                onClick={() =>
                  setPrefs((prev) => ({
                    ...prev,
                    tag: prev.tag === preset ? '' : preset,
                  }))
                }
              >
                {preset}
              </button>
            ))}
            <input
              className="tasks-chip-input"
              type="text"
              value={
                TAG_PRESETS.includes(prefs.tag as (typeof TAG_PRESETS)[number])
                  ? ''
                  : prefs.tag
              }
              onChange={(event) =>
                setPrefs((prev) => ({ ...prev, tag: event.target.value }))
              }
              placeholder="своя…"
              maxLength={64}
            />
          </div>
          <label className="tasks-chip-field">
            <span>Приоритет</span>
            <select
              value={prefs.priority}
              onChange={(event) =>
                setPrefs((prev) => ({
                  ...prev,
                  priority: event.target.value as SiteTaskPriority,
                }))
              }
            >
              <option value="low">Низкий</option>
              <option value="normal">Обычный</option>
              <option value="high">Высокий</option>
            </select>
          </label>
          <label className="tasks-chip-field">
            <span>Колонка</span>
            <select
              value={prefs.board}
              onChange={(event) =>
                setPrefs((prev) => ({
                  ...prev,
                  board: event.target.value as SiteTaskBoard,
                }))
              }
            >
              <option value="inbox">Разобрать</option>
              <option value="backlog">Бэклог</option>
              <option value="week">На эту неделю</option>
              <option value="today">Сегодня</option>
            </select>
          </label>
          <label className="tasks-chip-field">
            <span>Срок</span>
            <input
              type="date"
              value={prefs.dueAt}
              onChange={(event) =>
                setPrefs((prev) => ({ ...prev, dueAt: event.target.value }))
              }
            />
          </label>
          <label className="tasks-chip-field">
            <span>Время</span>
            <input
              type="time"
              value={prefs.dueTime}
              onChange={(event) =>
                setPrefs((prev) => ({ ...prev, dueTime: event.target.value }))
              }
            />
          </label>
          <label className="tasks-chip-field">
            <span>Повтор</span>
            <select
              value={prefs.repeatRule}
              onChange={(event) =>
                setPrefs((prev) => ({
                  ...prev,
                  repeatRule: event.target.value as SiteTaskRepeat,
                }))
              }
            >
              <option value="none">Нет</option>
              <option value="daily">Ежедневно</option>
              <option value="weekly">Еженедельно</option>
              <option value="monthly">Ежемесячно</option>
            </select>
          </label>
        </div>
      ) : null}
    </form>
  )
}
