import {
  QUIZ_PASS_PERCENT,
  STEP_LAB,
  STEP_QUIZ,
  STEP_READ,
  learnTargetFromNotes,
} from '@/components/tasks/learn-link'
import { flattenTasks } from '@/components/tasks/task-utils'
import {
  siteListUserTasks,
  siteUpdateUserTask,
  type SiteTaskChecklistItem,
  type SiteUserTask,
} from '@/data/site/site-api'

export type LearnSignals = {
  completedSlugs?: ReadonlySet<string> | null
  passedQuizSlugs?: ReadonlySet<string> | null
}

const STEP_IDS = new Set([STEP_READ, STEP_LAB, STEP_QUIZ])

export function checklistAfterSignals(
  task: SiteUserTask,
  signals: LearnSignals,
): { checklist: SiteTaskChecklistItem[]; completed: boolean } | null {
  if (task.completed) {
    return null
  }
  const target = learnTargetFromNotes(task.notes)
  if (!target) {
    return null
  }
  const passed = signals.passedQuizSlugs
  const doneSlugs = signals.completedSlugs

  if (target.kind === 'quiz') {
    if (passed?.has(target.slug)) {
      return { checklist: task.checklist, completed: true }
    }
    return null
  }

  const hasSteps = task.checklist.some((item) => STEP_IDS.has(item.id))
  if (!hasSteps) {
    if (doneSlugs?.has(target.slug)) {
      return { checklist: task.checklist, completed: true }
    }
    return null
  }

  let changed = false
  const checklist = task.checklist.map((item) => {
    let nextDone = item.done
    if (!item.done && item.id === STEP_READ && doneSlugs?.has(target.slug)) {
      nextDone = true
    }
    if (!item.done && item.id === STEP_LAB && doneSlugs?.has(target.slug)) {
      nextDone = true
    }
    if (!item.done && item.id === STEP_QUIZ && passed?.has(target.slug)) {
      nextDone = true
    }
    if (nextDone !== item.done) {
      changed = true
    }
    return nextDone === item.done ? item : { ...item, done: nextDone }
  })
  const completed = checklist.length > 0 && checklist.every((item) => item.done)
  if (!changed && !completed) {
    return null
  }
  return { checklist, completed }
}

export function passedQuizSlugSet(
  rows: Array<{ sourceKey?: string; score?: number; total?: number; percent?: number }>,
): Set<string> {
  const slugs = new Set<string>()
  for (const row of rows) {
    const key = (row.sourceKey || '').trim().toLowerCase()
    if (!key.startsWith('learn/')) {
      continue
    }
    const slug = key.slice('learn/'.length)
    if (!slug || slug.includes('/')) {
      continue
    }
    const percent =
      typeof row.percent === 'number'
        ? row.percent
        : row.total
          ? Math.round(((row.score || 0) / row.total) * 100)
          : 0
    if (percent >= QUIZ_PASS_PERCENT) {
      slugs.add(slug)
    }
  }
  return slugs
}

export async function syncLearnTasks(signals: LearnSignals): Promise<number> {
  const items = await siteListUserTasks()
  const updates = flattenTasks(items)
    .map((task) => {
      const next = checklistAfterSignals(task, signals)
      return next ? { id: task.id, ...next } : null
    })
    .filter((row): row is { id: number; checklist: SiteTaskChecklistItem[]; completed: boolean } =>
      row !== null,
    )
  await Promise.all(
    updates.map((row) =>
      siteUpdateUserTask(row.id, {
        checklist: row.checklist,
        completed: row.completed,
      }),
    ),
  )
  return updates.length
}
