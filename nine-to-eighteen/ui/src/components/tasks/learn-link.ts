import type { SiteTaskBoard, SiteTaskPriority, SiteUserTask } from '@/data/site/site-api'

export const LEARN_TASK_TAG = 'обучение'

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
  structured?: {
    quiz?: Array<{ question?: string; answer?: string }>
  } | null
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
  const label = post.shortTitle?.trim() || post.title.trim()
  const prefix = kind === 'quiz' ? 'Тест' : 'Статья'
  const title = `${prefix} · ${post.episode.trim()} · ${label}`.slice(0, 512)
  return {
    title,
    notes: notesWithLearnTarget(post.slug, kind),
    tag: LEARN_TASK_TAG,
    due_at: dueAt,
    priority: 'normal',
    board: 'today',
  }
}

export function wordingTaskDraft(
  title: string,
  dueAt: string,
): {
  title: string
  notes: string
  tag: string
  due_at: string
  priority: SiteTaskPriority
  board: SiteTaskBoard
} {
  return {
    title: title.trim().slice(0, 512),
    notes: '',
    tag: '',
    due_at: dueAt,
    priority: 'normal',
    board: 'today',
  }
}
