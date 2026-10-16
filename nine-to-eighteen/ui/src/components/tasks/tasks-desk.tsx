import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  siteCreateUserTask,
  siteDeleteUserTask,
  siteListUserTasks,
  siteUpdateUserTask,
  type SiteTaskBoard,
  type SiteTaskChecklistItem,
  type SiteTaskPriority,
  type SiteTaskRepeat,
  type SiteUserTask,
} from '@/data/site/site-api'
import { FocusTimer } from '@/components/tasks/focus-timer'
import { HabitsPanel } from '@/components/tasks/habits-panel'
import { NotesPanel } from '@/components/tasks/notes-panel'
import { TaskBoard } from '@/components/tasks/task-board'
import { TaskCalendar } from '@/components/tasks/task-calendar'
import { TaskEditor } from '@/components/tasks/task-editor'
import { TaskList } from '@/components/tasks/task-list'
import { TaskQuickAdd } from '@/components/tasks/task-quick-add'
import { dueReminders, isDueToday, isOverdue } from '@/components/tasks/task-utils'

type DeskView = 'list' | 'board' | 'calendar' | 'habits' | 'notes' | 'focus'
type StatusFilter = 'open' | 'done' | 'all'

const VIEWS: { id: DeskView; label: string }[] = [
  { id: 'list', label: 'Список' },
  { id: 'board', label: 'Доска' },
  { id: 'calendar', label: 'Календарь' },
  { id: 'habits', label: 'Привычки' },
  { id: 'notes', label: 'Заметки' },
  { id: 'focus', label: 'Фокус' },
]

export function TasksDesk() {
  const [items, setItems] = useState<SiteUserTask[]>([])
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [view, setView] = useState<DeskView>('list')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('open')
  const [tagFilter, setTagFilter] = useState('')
  const [search, setSearch] = useState('')
  const [creating, setCreating] = useState(false)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [defaultDueAt, setDefaultDueAt] = useState('')
  const [nowTick, setNowTick] = useState(() => Date.now())

  const refresh = useCallback(async () => {
    try {
      const next = await siteListUserTasks()
      setItems(next)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить задачи')
      setItems([])
    } finally {
      setReady(true)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    const id = window.setInterval(() => setNowTick(Date.now()), 60_000)
    return () => window.clearInterval(id)
  }, [])

  const tags = useMemo(() => {
    const set = new Set<string>()
    for (const item of items) {
      if (item.tag.trim()) {
        set.add(item.tag.trim())
      }
    }
    return [...set].sort((a, b) => a.localeCompare(b, 'ru'))
  }, [items])

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    return items.filter((item) => {
      if (statusFilter === 'open' && item.completed) {
        return false
      }
      if (statusFilter === 'done' && !item.completed) {
        return false
      }
      if (tagFilter && item.tag.trim() !== tagFilter) {
        return false
      }
      if (!query) {
        return true
      }
      const hay = `${item.title} ${item.notes} ${item.tag}`.toLowerCase()
      return hay.includes(query)
    })
  }, [items, statusFilter, tagFilter, search])

  const openCount = items.filter((item) => !item.completed).length
  const todayCount = items.filter((item) => isDueToday(item)).length
  const overdueCount = items.filter((item) => isOverdue(item)).length
  const reminders = useMemo(
    () => dueReminders(items, new Date(nowTick)),
    [items, nowTick],
  )

  const selected = useMemo(() => {
    if (selectedId == null) {
      return null
    }
    for (const item of items) {
      if (item.id === selectedId) {
        return item
      }
      const sub = item.subtasks?.find((row) => row.id === selectedId)
      if (sub) {
        return { ...sub, subtasks: [] }
      }
    }
    return null
  }, [items, selectedId])

  async function createTask(input: {
    title: string
    tag: string
    priority: SiteTaskPriority
    board: SiteTaskBoard
    due_at: string | null
    due_time: string | null
    repeat_rule: SiteTaskRepeat
    parent_id?: number | null
  }) {
    setCreating(true)
    setError('')
    try {
      await siteCreateUserTask(input)
      setDefaultDueAt('')
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать задачу')
    } finally {
      setCreating(false)
    }
  }

  async function toggleDone(task: SiteUserTask) {
    setBusyId(task.id)
    setError('')
    try {
      await siteUpdateUserTask(task.id, { completed: !task.completed })
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось обновить задачу')
    } finally {
      setBusyId(null)
    }
  }

  async function moveBoard(task: SiteUserTask, board: SiteTaskBoard) {
    setBusyId(task.id)
    try {
      await siteUpdateUserTask(task.id, { board })
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось перенести')
    } finally {
      setBusyId(null)
    }
  }

  async function saveTask(
    taskId: number,
    patch: {
      title?: string
      notes?: string
      tag?: string
      due_at?: string | null
      due_time?: string | null
      remind_at?: string | null
      priority?: SiteTaskPriority
      board?: SiteTaskBoard
      checklist?: SiteTaskChecklistItem[]
      repeat_rule?: SiteTaskRepeat
      completed?: boolean
    },
  ) {
    setBusyId(taskId)
    try {
      await siteUpdateUserTask(taskId, patch)
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить')
      throw err
    } finally {
      setBusyId(null)
    }
  }

  async function removeTask(task: SiteUserTask) {
    if (!window.confirm(`Удалить «${task.title}»?`)) {
      return
    }
    setBusyId(task.id)
    try {
      await siteDeleteUserTask(task.id)
      if (selectedId === task.id) {
        setSelectedId(null)
      }
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить')
    } finally {
      setBusyId(null)
    }
  }

  async function addSubtask(parentId: number, title: string) {
    await createTask({
      title,
      tag: '',
      priority: 'normal',
      board: 'backlog',
      due_at: null,
      due_time: null,
      repeat_rule: 'none',
      parent_id: parentId,
    })
  }

  if (!ready) {
    return <p className="learn-section-note">Загрузка задач…</p>
  }

  const showTaskViews = view === 'list' || view === 'board' || view === 'calendar'

  return (
    <section className="tasks-desk" aria-labelledby="tasks-desk-title">
      <header className="tasks-desk-head">
        <div>
          <h2 id="tasks-desk-title" className="learn-section-title">
            Мои задачи
          </h2>
          <p className="learn-section-note">
            Быстрый ввод, доска, календарь, привычки и фокус — отдельно от Learn.
          </p>
        </div>
        <div className="tasks-desk-stats" aria-label="Сводка">
          <span>
            <strong>{openCount}</strong> открыто
          </span>
          <span>
            <strong>{todayCount}</strong> сегодня
          </span>
          <span className={overdueCount ? 'is-warn' : undefined}>
            <strong>{overdueCount}</strong> просрочено
          </span>
        </div>
      </header>

      {reminders.length > 0 ? (
        <div className="tasks-reminders" role="status">
          <strong>Напоминания</strong>
          <ul>
            {reminders.slice(0, 5).map((task) => (
              <li key={task.id}>
                <button type="button" onClick={() => setSelectedId(task.id)}>
                  {task.title}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="tasks-view-tabs" role="tablist" aria-label="Виды рабочего стола">
        {VIEWS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={view === item.id}
            className={view === item.id ? 'tasks-view-tab is-active' : 'tasks-view-tab'}
            onClick={() => setView(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {showTaskViews ? (
        <>
          <TaskQuickAdd
            busy={creating}
            defaultDueAt={defaultDueAt}
            onCreate={createTask}
          />
          <div className="learn-filters" aria-label="Фильтры задач">
            <label className="learn-filter-field">
              <span>Статус</span>
              <select
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value as StatusFilter)
                }
              >
                <option value="open">Открытые</option>
                <option value="done">Готовые</option>
                <option value="all">Все</option>
              </select>
            </label>
            <label className="learn-filter-field">
              <span>Метка</span>
              <select
                value={tagFilter}
                onChange={(event) => setTagFilter(event.target.value)}
              >
                <option value="">Все</option>
                {tags.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
            <label className="learn-filter-field tasks-search-field">
              <span>Поиск</span>
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Название, заметка…"
              />
            </label>
          </div>
        </>
      ) : null}

      {error ? <p className="tasks-personal-error">{error}</p> : null}

      <div className={selected ? 'tasks-desk-body has-editor' : 'tasks-desk-body'}>
        <div className="tasks-desk-main">
          {view === 'list' ? (
            <TaskList
              items={filtered}
              onToggle={(task) => void toggleDone(task)}
              onOpen={(task) => setSelectedId(task.id)}
            />
          ) : null}
          {view === 'board' ? (
            <TaskBoard
              items={filtered}
              onToggle={(task) => void toggleDone(task)}
              onOpen={(task) => setSelectedId(task.id)}
              onMove={(task, board) => void moveBoard(task, board)}
            />
          ) : null}
          {view === 'calendar' ? (
            <TaskCalendar
              items={items}
              onToggle={(task) => void toggleDone(task)}
              onOpen={(task) => setSelectedId(task.id)}
              onPickDay={(iso) => {
                setDefaultDueAt(iso)
                setView('list')
              }}
            />
          ) : null}
          {view === 'habits' ? <HabitsPanel /> : null}
          {view === 'notes' ? <NotesPanel /> : null}
          {view === 'focus' ? <FocusTimer /> : null}
        </div>
        {selected && showTaskViews ? (
          <TaskEditor
            task={selected}
            busy={busyId === selected.id || creating}
            onClose={() => setSelectedId(null)}
            onSave={saveTask}
            onDelete={removeTask}
            onAddSubtask={addSubtask}
          />
        ) : null}
      </div>
    </section>
  )
}
