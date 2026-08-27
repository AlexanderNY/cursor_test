import type { LearnEpisode, LearnLink, LearnRubricId } from '@/data/learn/types'
import { learnEpisodes } from '@/data/learn/episodes'

const STORAGE_KEY = 'nine-to-eighteen-learn-v1'

export type LearnContentFormat = 'markdown' | 'html'

export type LearnPost = LearnEpisode & {
  theoryFormat: LearnContentFormat
  labFormat: LearnContentFormat
  cheatsheetFormat: LearnContentFormat
  publishedAt: string
  updatedAt: string
}

export type LearnPostInput = {
  slug: string
  episode: string
  title: string
  shortTitle: string
  rubricId: LearnRubricId
  order: number
  theory: string
  lab: string
  cheatsheet: string
  diagram: string
  links: LearnLink[]
  theoryFormat: LearnContentFormat
  labFormat: LearnContentFormat
  cheatsheetFormat: LearnContentFormat
  publishedAt: string
}

function seedPublishedAt(order: number, baseMs: number): string {
  // Seed already visible: staggered 1 day apart ending today.
  const offsetDays = Math.max(0, learnEpisodes.length - order)
  return new Date(baseMs - offsetDays * 24 * 60 * 60 * 1000).toISOString()
}

function seedPosts(): LearnPost[] {
  const now = Date.now()
  const updatedAt = new Date(now).toISOString()
  return learnEpisodes.map((episode) => ({
    ...episode,
    theoryFormat: 'markdown',
    labFormat: 'markdown',
    cheatsheetFormat: 'markdown',
    publishedAt: seedPublishedAt(episode.order, now),
    updatedAt,
  }))
}

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function normalizePost(raw: Partial<LearnPost> & LearnEpisode): LearnPost {
  const fallbackPublished = raw.updatedAt || new Date().toISOString()
  return {
    ...raw,
    theoryFormat: raw.theoryFormat === 'html' ? 'html' : 'markdown',
    labFormat: raw.labFormat === 'html' ? 'html' : 'markdown',
    cheatsheetFormat: raw.cheatsheetFormat === 'html' ? 'html' : 'markdown',
    publishedAt: raw.publishedAt || fallbackPublished,
    updatedAt: raw.updatedAt || new Date().toISOString(),
    links: Array.isArray(raw.links) ? raw.links : [],
  }
}

function readRaw(): { posts: LearnPost[]; needsMigration: boolean } | null {
  if (!isBrowser()) {
    return null
  }
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as Array<Partial<LearnPost> & LearnEpisode>
    if (!Array.isArray(parsed)) {
      return null
    }
    const needsMigration = parsed.some((item) => !item.publishedAt)
    return {
      posts: parsed.map((item) => normalizePost(item)),
      needsMigration,
    }
  } catch {
    return null
  }
}

function writeRaw(posts: LearnPost[]): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(posts))
}

export function loadLearnPosts(): LearnPost[] {
  const stored = readRaw()
  if (stored && stored.posts.length > 0) {
    const normalized = [...stored.posts].sort((a, b) => a.order - b.order)
    if (stored.needsMigration) {
      writeRaw(normalized)
    }
    return normalized
  }
  const seeded = seedPosts()
  writeRaw(seeded)
  return seeded
}

export function getLearnPostBySlug(slug: string): LearnPost | undefined {
  return loadLearnPosts().find((post) => post.slug === slug)
}

export function saveLearnPost(input: LearnPostInput): LearnPost {
  const posts = loadLearnPosts()
  const updatedAt = new Date().toISOString()
  const next: LearnPost = {
    ...input,
    publishedAt: new Date(input.publishedAt).toISOString(),
    updatedAt,
  }
  const index = posts.findIndex((post) => post.slug === input.slug)
  if (index >= 0) {
    posts[index] = next
  } else {
    posts.push(next)
  }
  writeRaw(posts.sort((a, b) => a.order - b.order))
  return next
}

export function deleteLearnPost(slug: string): void {
  const posts = loadLearnPosts().filter((post) => post.slug !== slug)
  writeRaw(posts)
}

export function resetLearnPostsToSeed(): LearnPost[] {
  const seeded = seedPosts()
  writeRaw(seeded)
  return seeded
}

/** Assign publishedAt for all posts by order: start + (index * intervalDays). */
export function scheduleAllLearnPosts(startIso: string, intervalDays: number): LearnPost[] {
  const startMs = new Date(startIso).getTime()
  if (Number.isNaN(startMs)) {
    throw new Error('Некорректная дата начала')
  }
  const step = Math.max(0, intervalDays) * 24 * 60 * 60 * 1000
  const updatedAt = new Date().toISOString()
  const posts = loadLearnPosts()
    .sort((a, b) => a.order - b.order)
    .map((post, index) => ({
      ...post,
      publishedAt: new Date(startMs + index * step).toISOString(),
      updatedAt,
    }))
  writeRaw(posts)
  return posts
}

export function isPostPublished(post: Pick<LearnPost, 'publishedAt'>, now = Date.now()): boolean {
  const publishedMs = new Date(post.publishedAt).getTime()
  if (Number.isNaN(publishedMs)) {
    return true
  }
  return publishedMs <= now
}

export function formatPublishDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function toDatetimeLocalValue(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return toDatetimeLocalValue(new Date().toISOString())
  }
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function fromDatetimeLocalValue(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return new Date().toISOString()
  }
  return date.toISOString()
}

export function slugifyTitle(title: string): string {
  const map: Record<string, string> = {
    а: 'a',
    б: 'b',
    в: 'v',
    г: 'g',
    д: 'd',
    е: 'e',
    ё: 'e',
    ж: 'zh',
    з: 'z',
    и: 'i',
    й: 'y',
    к: 'k',
    л: 'l',
    м: 'm',
    н: 'n',
    о: 'o',
    п: 'p',
    р: 'r',
    с: 's',
    т: 't',
    у: 'u',
    ф: 'f',
    х: 'h',
    ц: 'c',
    ч: 'ch',
    ш: 'sh',
    щ: 'sch',
    ъ: '',
    ы: 'y',
    ь: '',
    э: 'e',
    ю: 'yu',
    я: 'ya',
  }
  return title
    .trim()
    .toLowerCase()
    .split('')
    .map((char) => map[char] ?? char)
    .join('')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64)
}

export function createEmptyPost(order: number): LearnPostInput {
  const publishedAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
  return {
    slug: `post-${Date.now()}`,
    episode: `S01E${String(order).padStart(2, '0')}`,
    title: 'Новая запись',
    shortTitle: 'Новая',
    rubricId: 'architecture',
    order,
    theory: '<p>Текст теории</p>',
    lab: '<p>Условие лабы</p>',
    cheatsheet: '<p>Шпаргалка</p>',
    diagram: 'flowchart LR\n  A[Старт] --> B[Финиш]',
    links: [],
    theoryFormat: 'html',
    labFormat: 'html',
    cheatsheetFormat: 'html',
    publishedAt,
  }
}
