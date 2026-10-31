import type {
  SiteTaskBoard,
  SiteTaskChecklistItem,
  SiteTaskPriority,
  SiteUserTask,
} from '@/data/site/site-api'

export const LEARN_TASK_TAG = 'обучение'
export const QUIZ_PASS_PERCENT = 70
export const PLAN_FALLBACK_MIN = 15
export const PLAN_TASK_CAP = 6
export const STEP_READ = 'step-read'
export const STEP_LAB = 'step-lab'
export const STEP_QUIZ = 'step-quiz'

const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/
const MARKER_RE = /^learn:([a-z0-9]+(?:-[a-z0-9]+)*)(?:#(quiz))?$/i

export type LearnTaskKind = 'article' | 'quiz'

export type LearnTaskTarget = {
  slug: string
  kind: LearnTaskKind
}

export type LearnTaskSource = {
  slug: string
  episode: string
  title: string
  shortTitle?: string
  durationMin?: number
  lab?: string
  structured?: {
    lab?: string
    quiz?: Array<{ question?: string; answer?: string }>
  } | null
}

export function postHasLab(post: LearnTaskSource): boolean {
  return Boolean((post.lab || '').trim() || (post.structured?.lab || '').trim())
}

export function postHasQuiz(post: LearnTaskSource): boolean {
  const quiz = post.structured?.quiz
  if (!Array.isArray(quiz)) {
    return false
  }
  return quiz.some((row) => Boolean(row.question?.trim() && row.answer?.trim()))
}

export function learnTargetFromNotes(notes: string): LearnTaskTarget | null {
  for (const line of notes.split('\n')) {
    const match = MARKER_RE.exec(line.trim())
    if (!match) {
      continue
    }
    return {
      slug: match[1].toLowerCase(),
      kind: match[2] ? 'quiz' : 'article',
    }
  }
  return null
}

export function learnSlugFromNotes(notes: string): string {
  return learnTargetFromNotes(notes)?.slug || ''
}

export function learnSlugQueued(keys: ReadonlySet<string>, slug: string): boolean {
  const clean = slug.trim().toLowerCase()
  if (!clean) {
    return false
  }
  for (const key of keys) {
    if (key.split('#')[0] === clean) {
      return true
    }
  }
  return false
}

export function learnTaskKey(slug: string, kind: LearnTaskKind = 'article'): string {
  const clean = slug.trim().toLowerCase()
  if (!SLUG_RE.test(clean)) {
    return ''
  }
  return kind === 'quiz' ? `${clean}#quiz` : clean
}

/** Notes shown in the card. The learn:slug line stays in storage. */
export function displayNotes(notes: string): string {
  return notes
    .split('\n')
    .filter((line) => !line.trim().toLowerCase().startsWith('learn:'))
    .join('\n')
    .trim()
}

export function notesWithLearnTarget(
  slug: string,
  kind: LearnTaskKind,
  notes = '',
): string {
  const clean = slug.trim().toLowerCase()
  const rest = displayNotes(notes)
  if (!SLUG_RE.test(clean)) {
    return rest
  }
  const marker = kind === 'quiz' ? `learn:${clean}#quiz` : `learn:${clean}`
  return rest ? `${marker}\n${rest}` : marker
}

export function notesWithLearnSlug(
  slug: string,
  notes = '',
  kind: LearnTaskKind = 'article',
): string {
  return notesWithLearnTarget(slug, kind, notes)
}

export function learnEpisodePath(
  slug: string,
  part?: 'lab' | 'quiz' | 'anki',
): string {
  if (part === 'lab') {
    return `/game/learn/${slug}?tab=lab`
  }
  if (part === 'quiz') {
    return `/game/learn/${slug}#sp-quiz`
  }
  if (part === 'anki') {
    return `/game/learn/${slug}#sp-summary`
  }
  return `/game/learn/${slug}`
}

export function openLearnKeys(items: SiteUserTask[]): Set<string> {
  const keys = new Set<string>()
  const walk = (task: SiteUserTask) => {
    if (!task.completed) {
      const target = learnTargetFromNotes(task.notes)
      if (target) {
        const key = learnTaskKey(target.slug, target.kind)
        if (key) {
          keys.add(key)
        }
      }
    }
    for (const sub of task.subtasks || []) {
      walk(sub)
    }
  }
  for (const item of items) {
    walk(item)
  }
  return keys
}

export function episodeSteps(post: LearnTaskSource): SiteTaskChecklistItem[] {
  const steps: SiteTaskChecklistItem[] = [
    { id: STEP_READ, title: 'Прочитать', done: false },
  ]
  if (postHasLab(post)) {
    steps.push({ id: STEP_LAB, title: 'Лаба', done: false })
  }
  if (postHasQuiz(post)) {
    steps.push({ id: STEP_QUIZ, title: 'Тест', done: false })
  }
  return steps
}

export function episodeTaskDraft(
  post: LearnTaskSource,
  options: { board: SiteTaskBoard; dueAt: string | null },
): {
  title: string
  notes: string
  tag: string
  due_at: string | null
  priority: SiteTaskPriority
  board: SiteTaskBoard
  checklist: SiteTaskChecklistItem[]
} {
  const label = post.shortTitle?.trim() || post.title.trim()
  const title = `${post.episode.trim()} · ${label}`.slice(0, 512)
  return {
    title,
    notes: notesWithLearnTarget(post.slug, 'article'),
    tag: LEARN_TASK_TAG,
    due_at: options.dueAt,
    priority: 'normal',
    board: options.board,
    checklist: episodeSteps(post),
  }
}

export function learnTaskDraft(
  post: LearnTaskSource,
  dueAt: string,
  kind: LearnTaskKind = 'article',
): {
  title: string
  notes: string
  tag: string
  due_at: string
  priority: SiteTaskPriority
  board: SiteTaskBoard
} {
  if (kind === 'article') {
    return {
      ...episodeTaskDraft(post, { board: 'inbox', dueAt: null }),
      due_at: dueAt,
    }
  }
  const label = post.shortTitle?.trim() || post.title.trim()
  const title = `Тест · ${post.episode.trim()} · ${label}`.slice(0, 512)
  return {
    title,
    notes: notesWithLearnTarget(post.slug, kind),
    tag: LEARN_TASK_TAG,
    due_at: dueAt,
    priority: 'normal',
    board: 'inbox',
  }
}

export function wordingTaskDraft(
  title: string,
  _dueAt: string,
): {
  title: string
  notes: string
  tag: string
  due_at: string | null
  priority: SiteTaskPriority
  board: SiteTaskBoard
} {
  return {
    title: title.trim().slice(0, 512),
    notes: '',
    tag: '',
    due_at: null,
    priority: 'normal',
    board: 'inbox',
  }
}

export function appendFocusNote(notes: string, minutes: number): string {
  const line = `Фокус: ${minutes} мин`
  const target = learnTargetFromNotes(notes)
  const rest = displayNotes(notes)
  const next = rest ? `${rest}\n${line}` : line
  if (!target) {
    return next
  }
  return notesWithLearnTarget(target.slug, target.kind, next)
}

function planCost(post: LearnTaskSource): number {
  return post.durationMin && post.durationMin > 0 ? post.durationMin : PLAN_FALLBACK_MIN
}

/** Greedy fill of unfinished episodes that fit the minute budget. */
export function planEpisodes<T extends LearnTaskSource>(
  posts: T[],
  openSlugs: ReadonlySet<string>,
  minutes: number,
): T[] {
  const budget = Math.round(minutes)
  if (budget <= 0) {
    return []
  }
  const candidates = posts.filter((post) => !openSlugs.has(post.slug.trim().toLowerCase()))
  const picked: T[] = []
  let used = 0
  for (const post of candidates) {
    if (picked.length >= PLAN_TASK_CAP) {
      break
    }
    const cost = planCost(post)
    if (used + cost > budget) {
      continue
    }
    picked.push(post)
    used += cost
  }
  if (picked.length === 0 && candidates.length > 0) {
    const shortest = [...candidates].sort((a, b) => planCost(a) - planCost(b))[0]
    if (shortest) {
      picked.push(shortest)
    }
  }
  return picked
}
