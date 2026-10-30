import type { SiteTaskBoard, SiteTaskPriority, SiteUserTask } from '@/data/site/site-api'

export const LEARN_TASK_TAG = 'обучение'

const SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/

export type LearnTaskSource = {
  slug: string
  episode: string
  title: string
  shortTitle?: string
}

export function learnSlugFromNotes(notes: string): string {
  for (const line of notes.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed.toLowerCase().startsWith('learn:')) {
      continue
    }
    const slug = trimmed.slice('learn:'.length).trim().toLowerCase()
    if (SLUG_RE.test(slug)) {
      return slug
    }
  }
  return ''
}

/** Notes shown in the card. The learn:slug line stays in storage. */
export function displayNotes(notes: string): string {
  return notes
    .split('\n')
    .filter((line) => !line.trim().toLowerCase().startsWith('learn:'))
    .join('\n')
    .trim()
}

export function notesWithLearnSlug(slug: string, notes = ''): string {
  const clean = slug.trim().toLowerCase()
  const rest = displayNotes(notes)
  if (!SLUG_RE.test(clean)) {
    return rest
  }
  return rest ? `learn:${clean}\n${rest}` : `learn:${clean}`
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

export function openLearnSlugs(items: SiteUserTask[]): Set<string> {
  const slugs = new Set<string>()
  const walk = (task: SiteUserTask) => {
    if (!task.completed) {
      const slug = learnSlugFromNotes(task.notes)
      if (slug) {
        slugs.add(slug)
      }
    }
    for (const sub of task.subtasks || []) {
      walk(sub)
    }
  }
  for (const item of items) {
    walk(item)
  }
  return slugs
}

export function learnTaskDraft(
  post: LearnTaskSource,
  dueAt: string,
): {
  title: string
  notes: string
  tag: string
  due_at: string
  priority: SiteTaskPriority
  board: SiteTaskBoard
} {
  const label = post.shortTitle?.trim() || post.title.trim()
  const title = `${post.episode.trim()} · ${label}`.slice(0, 512)
  return {
    title,
    notes: notesWithLearnSlug(post.slug),
    tag: LEARN_TASK_TAG,
    due_at: dueAt,
    priority: 'normal',
    board: 'today',
  }
}
