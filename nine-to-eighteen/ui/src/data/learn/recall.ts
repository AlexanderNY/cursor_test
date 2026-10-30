/** Interview recall: said in 7 days, stumbled in 3, missed tomorrow. */

export const LEARN_PROFILE_FILTER_KEY = 'learn-profile-filter'
export const LEARN_LEVEL_FILTER_KEY = 'learn-level-filter'
export const RECALL_STORAGE_KEY = 'learn-recall-v1'

export const RECALL_NEW_LIMIT = 8

export function interviewRecallId(slug: string, question: string): string {
  return `q:${slug}:${question.trim()}`
}

export type RecallMark = 'missed' | 'stumbled' | 'said'

export const RECALL_INTERVAL_DAYS: Record<RecallMark, number> = {
  missed: 1,
  stumbled: 3,
  said: 7,
}

const MARK_RANK: Record<RecallMark, number> = {
  missed: 0,
  stumbled: 1,
  said: 2,
}

const MARKS = new Set<RecallMark>(['missed', 'stumbled', 'said'])

export type RecallEntry = {
  mark: RecallMark
  reviewedAt: number
  dueAt: number
}

export type RecallStore = Record<string, RecallEntry>

export function dueAtFor(mark: RecallMark, reviewedAt: number): number {
  const due = new Date(reviewedAt)
  due.setDate(due.getDate() + RECALL_INTERVAL_DAYS[mark])
  due.setHours(0, 0, 0, 0)
  return due.getTime()
}

export function parseRecallStore(raw: unknown): RecallStore {
  if (!raw || typeof raw !== 'object') {
    return {}
  }
  const store: RecallStore = {}
  for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
    if (!key || !value || typeof value !== 'object') {
      continue
    }
    const row = value as Record<string, unknown>
    const mark = row.mark
    if (typeof mark !== 'string' || !MARKS.has(mark as RecallMark)) {
      continue
    }
    if (typeof row.reviewedAt !== 'number' || typeof row.dueAt !== 'number') {
      continue
    }
    store[key] = {
      mark: mark as RecallMark,
      reviewedAt: row.reviewedAt,
      dueAt: row.dueAt,
    }
  }
  return store
}

export function readRecallStore(): RecallStore {
  if (typeof window === 'undefined') {
    return {}
  }
  try {
    return parseRecallStore(JSON.parse(window.localStorage.getItem(RECALL_STORAGE_KEY) || '{}'))
  } catch {
    return {}
  }
}

export function writeRecallMark(id: string, mark: RecallMark, now = Date.now()): RecallStore {
  const store = readRecallStore()
  store[id] = {
    mark,
    reviewedAt: now,
    dueAt: dueAtFor(mark, now),
  }
  window.localStorage.setItem(RECALL_STORAGE_KEY, JSON.stringify(store))
  return store
}

export function isRecallDue(entry: RecallEntry | undefined, now: number): boolean {
  return Boolean(entry && entry.dueAt <= now)
}

export type RecallSessionStats = {
  missed: number
  stumbled: number
  said: number
  fresh: number
}

export function recallSessionStats(
  ids: string[],
  store: RecallStore,
  now: number,
): RecallSessionStats {
  const stats: RecallSessionStats = { missed: 0, stumbled: 0, said: 0, fresh: 0 }
  for (const id of ids) {
    const entry = store[id]
    if (!entry) {
      stats.fresh += 1
      continue
    }
    if (entry.dueAt > now) {
      continue
    }
    stats[entry.mark] += 1
  }
  return stats
}

export function buildRecallSession<T extends { id: string }>(
  items: T[],
  store: RecallStore,
  now: number,
  newLimit = RECALL_NEW_LIMIT,
): T[] {
  const due: T[] = []
  const fresh: T[] = []
  for (const item of items) {
    const entry = store[item.id]
    if (!entry) {
      fresh.push(item)
      continue
    }
    if (entry.dueAt <= now) {
      due.push(item)
    }
  }
  due.sort((left, right) => {
    const leftEntry = store[left.id]
    const rightEntry = store[right.id]
    if (!leftEntry || !rightEntry) {
      return 0
    }
    const rank = MARK_RANK[leftEntry.mark] - MARK_RANK[rightEntry.mark]
    if (rank !== 0) {
      return rank
    }
    return leftEntry.dueAt - rightEntry.dueAt
  })
  return [...due, ...fresh.slice(0, newLimit)]
}

export function formatRecallDay(dueAt: number): string {
  return new Date(dueAt).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}
