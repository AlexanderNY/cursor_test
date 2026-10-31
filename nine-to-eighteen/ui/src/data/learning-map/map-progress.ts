import type { LearnPost } from '@/data/learn/learn-store'
import type { LeafNote } from '@/data/learning-map/leaf-notes'
import type { MindNode } from '@/data/learning-map/parse-outline'
import type { SiteAnkiCardState } from '@/data/site/site-api'
import { learnAnkiCards } from '@/data/site/structured-post'

/** Состояние листа со статьёй: не начат, прочитан, пора повторить. */
export type StudyState = 'none' | 'new' | 'done' | 'due'

export type StudyRollup = {
  done: number
  total: number
  due: number
  state: StudyState
}

export type GapKind = 'article' | 'anki' | 'note'

const GAP_LABEL: Record<GapKind, string> = {
  article: 'нет статьи',
  anki: 'нет карточки',
  note: 'нет заметки',
}

export function gapLabel(kind: GapKind): string {
  return GAP_LABEL[kind]
}

export function slugOf(node: MindNode): string {
  return (node.learnSlug || '').trim().toLowerCase()
}

export function slugFromAnkiState(card: SiteAnkiCardState): string {
  const source = (card.sourceKey || '').trim()
  if (source.startsWith('learn/')) {
    return source.slice('learn/'.length).toLowerCase()
  }
  const id = (card.cardId || '').trim()
  if (id.startsWith('learn:')) {
    return (id.split(':')[1] || '').toLowerCase()
  }
  return ''
}

/** Слаги, у которых есть хотя бы одна просроченная карточка. */
export function dueSlugSet(cards: SiteAnkiCardState[], now = Date.now()): Set<string> {
  return new Set(dueCountBySlug(cards, now).keys())
}

/** Число просроченных карточек по slug выпуска Learn. */
export function dueCountBySlug(
  cards: SiteAnkiCardState[],
  now = Date.now(),
): Map<string, number> {
  const counts = new Map<string, number>()
  for (const card of cards) {
    const slug = slugFromAnkiState(card)
    if (!slug) {
      continue
    }
    const dueAt = Date.parse(card.dueAt)
    if (Number.isNaN(dueAt) || dueAt > now) {
      continue
    }
    counts.set(slug, (counts.get(slug) || 0) + 1)
  }
  return counts
}

function leafState(slug: string, completed: ReadonlySet<string>, due: ReadonlySet<string>): StudyState {
  if (!slug) {
    return 'none'
  }
  if (due.has(slug)) {
    return 'due'
  }
  if (completed.has(slug)) {
    return 'done'
  }
  return 'new'
}

function combineBranch(done: number, total: number, due: number): StudyState {
  if (total <= 0) {
    return 'none'
  }
  if (due > 0) {
    return 'due'
  }
  if (done >= total) {
    return 'done'
  }
  return 'new'
}

/** Доля пройденных статей в поддереве. Лист без статьи в счёт не входит. */
export function buildProgressIndex(
  root: MindNode,
  completed: ReadonlySet<string>,
  due: ReadonlySet<string>,
): Map<string, StudyRollup> {
  const index = new Map<string, StudyRollup>()

  const walk = (node: MindNode): StudyRollup => {
    const slug = node.id === 'root' ? '' : slugOf(node)
    const own = leafState(slug, completed, due)
    let done = slug && completed.has(slug) ? 1 : 0
    let total = slug ? 1 : 0
    let dueCount = own === 'due' ? 1 : 0

    for (const child of node.children) {
      const childRollup = walk(child)
      done += childRollup.done
      total += childRollup.total
      dueCount += childRollup.due
    }
    const state = total <= 1 && slug ? own : combineBranch(done, total, dueCount)
    const rollup: StudyRollup = {
      done,
      total,
      due: dueCount,
      state,
    }
    index.set(node.id, rollup)
    return rollup
  }

  walk(root)
  return index
}

export function studyCaption(rollup: StudyRollup | undefined): string {
  if (!rollup || rollup.total <= 0 || rollup.state === 'none') {
    return ''
  }
  if (rollup.total === 1) {
    if (rollup.state === 'due') {
      return 'Пора повторить'
    }
    if (rollup.state === 'done') {
      return 'Прочитано'
    }
    if (rollup.state === 'new') {
      return 'Не начато'
    }
  }
  if (rollup.state === 'due') {
    return `Пройдено ${rollup.done} из ${rollup.total} · к повторению ${rollup.due}`
  }
  if (rollup.done >= rollup.total) {
    return `Пройдено ${rollup.done} из ${rollup.total}`
  }
  return `Пройдено ${rollup.done} из ${rollup.total}`
}

function isUnfinishedArticle(
  node: MindNode,
  completed: ReadonlySet<string>,
  due: ReadonlySet<string>,
): boolean {
  if (node.id === 'root') {
    return false
  }
  const slug = slugOf(node)
  if (!slug) {
    return false
  }
  return due.has(slug) || !completed.has(slug)
}

/** Оставляет непрочитанные статьи и листья с просроченными карточками. */
export function filterUnfinished(
  node: MindNode,
  completed: ReadonlySet<string>,
  due: ReadonlySet<string>,
): MindNode | null {
  const children = node.children
    .map((child) => filterUnfinished(child, completed, due))
    .filter((child): child is MindNode => child !== null)
  if (isUnfinishedArticle(node, completed, due)) {
    return { ...node, children }
  }
  if (children.length === 0) {
    return null
  }
  return { ...node, children }
}

/** Первый непройденный лист в порядке оглавления. */
export function findNextUnfinished(
  node: MindNode,
  completed: ReadonlySet<string>,
  due: ReadonlySet<string>,
): MindNode | null {
  if (isUnfinishedArticle(node, completed, due)) {
    return node
  }
  if (node.children.length === 0) {
    return null
  }
  for (const child of node.children) {
    const found = findNextUnfinished(child, completed, due)
    if (found) {
      return found
    }
  }
  return null
}

function hasAnkiContent(
  node: MindNode,
  note: LeafNote | undefined,
  post: LearnPost | undefined,
  deckSlugs: ReadonlySet<string>,
): boolean {
  const slug = slugOf(node)
  if (slug && deckSlugs.has(slug)) {
    return true
  }
  if (post?.structured) {
    return learnAnkiCards(post.structured).length > 0
  }
  const back = (note?.description || node.description || post?.theory || '').trim()
  return Boolean(back)
}

function hasWrittenNote(node: MindNode, note: LeafNote | undefined): boolean {
  if ((node.description || '').trim()) {
    return true
  }
  if (!note) {
    return false
  }
  return Boolean(note.description.trim() || note.tags.length > 0)
}

/** Дыры листа: нет статьи, нет карточки или нет заметки. Ветки не помечаются. */
export function buildGapIndex(
  root: MindNode,
  notes: Record<string, LeafNote>,
  posts: LearnPost[],
  postsReady: boolean,
  deckSlugs: ReadonlySet<string>,
): Map<string, GapKind[]> {
  const postsBySlug = new Map(posts.map((post) => [post.slug.toLowerCase(), post]))
  const index = new Map<string, GapKind[]>()

  const walk = (node: MindNode): void => {
    for (const child of node.children) {
      walk(child)
    }
    if (node.id === 'root') {
      return
    }
    const slug = slugOf(node)
    if (!slug) {
      return
    }
    const isLeaf = node.children.length === 0
    const post = postsBySlug.get(slug)
    const gaps: GapKind[] = []
    const articleKnown = !slug || postsReady
    const articleOk = Boolean(slug) && (!postsReady || Boolean(post))
    if (articleKnown && !articleOk) {
      gaps.push('article')
    }
    if (!hasAnkiContent(node, notes[node.id], post, deckSlugs)) {
      gaps.push('anki')
    }
    if (isLeaf && !hasWrittenNote(node, notes[node.id])) {
      gaps.push('note')
    }
    if (gaps.length > 0) {
      index.set(node.id, gaps)
    }
  }

  walk(root)
  return index
}

export function gapTone(gaps: GapKind[] | undefined): 'hard' | 'soft' | 'note' | null {
  if (!gaps || gaps.length === 0) {
    return null
  }
  const missingStudy = gaps.includes('article') && gaps.includes('anki')
  if (missingStudy) {
    return 'hard'
  }
  if (gaps.includes('article') || gaps.includes('anki')) {
    return 'soft'
  }
  return 'note'
}
