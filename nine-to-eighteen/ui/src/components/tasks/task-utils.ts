import type {
  SiteTaskBoard,
  SiteTaskPriority,
  SiteUserTask,
} from '@/data/site/site-api'

export const TAG_PRESETS = ['работа', 'дом', 'обучение'] as const

export const BOARD_COLUMNS: { id: SiteTaskBoard; label: string }[] = [
  { id: 'backlog', label: 'Бэклог' },
  { id: 'week', label: 'На эту неделю' },
  { id: 'today', label: 'Сегодня' },
  { id: 'done', label: 'Сделано' },
]

export function formatDue(iso: string | null, time: string | null = null): string {
  if (!iso) {
    return ''
  }
  const date = new Date(`${iso}T12:00:00`)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  const label = date.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  })
  return time ? `${label} · ${time}` : label
}

export function isOverdue(task: SiteUserTask): boolean {
  if (task.completed || !task.dueAt) {
    return false
  }
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(`${task.dueAt}T12:00:00`)
  return due < today
}

export function isDueToday(task: SiteUserTask): boolean {
  if (!task.dueAt || task.completed) {
    return false
  }
  const today = new Date()
  const y = today.getFullYear()
  const m = String(today.getMonth() + 1).padStart(2, '0')
  const d = String(today.getDate()).padStart(2, '0')
  return task.dueAt === `${y}-${m}-${d}`
}

export function checklistProgress(task: SiteUserTask): { done: number; total: number } {
  const items = task.checklist || []
  const total = items.length
  const done = items.filter((item) => item.done).length
  return { done, total }
}

export function tagAccentClass(tag: string): string {
  const key = tag.trim().toLowerCase()
  if (key === 'работа' || key === 'work') {
    return 'tasks-tag-work'
  }
  if (key === 'дом' || key === 'home') {
    return 'tasks-tag-home'
  }
  if (key === 'обучение' || key === 'learn' || key === 'учеба' || key === 'учёба') {
    return 'tasks-tag-learn'
  }
  return 'tasks-tag-other'
}

export function priorityLabel(priority: SiteTaskPriority): string {
  if (priority === 'high') {
    return 'Высокий'
  }
  if (priority === 'low') {
    return 'Низкий'
  }
  return 'Обычный'
}

export function flattenTasks(items: SiteUserTask[]): SiteUserTask[] {
  const out: SiteUserTask[] = []
  for (const item of items) {
    out.push(item)
    if (item.subtasks?.length) {
      out.push(...item.subtasks)
    }
  }
  return out
}

export function dueReminders(items: SiteUserTask[], now = new Date()): SiteUserTask[] {
  return flattenTasks(items).filter((task) => {
    if (task.completed || !task.remindAt) {
      return false
    }
    const at = new Date(task.remindAt)
    return !Number.isNaN(at.getTime()) && at <= now
  })
}

export function isoDate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function startOfWeek(d: Date): Date {
  const copy = new Date(d)
  copy.setHours(0, 0, 0, 0)
  const day = (copy.getDay() + 6) % 7 // Monday=0
  copy.setDate(copy.getDate() - day)
  return copy
}

export function newChecklistId(): string {
  return `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
}
