import type { LearnEpisode, LearnLink, LearnRubricId } from '@/data/learn/types'
import { learnEpisodes } from '@/data/learn/episodes'
import type { LearnLevelId, LearnProfileId } from '@/data/learn/labels'
import {
  normalizeLevel,
  normalizeProfiles,
  normalizeStringList,
} from '@/data/learn/labels'
import {
  apiDeletePost,
  apiGetPublishedPost,
  apiListAdminPosts,
  apiListPublishedPosts,
  apiResetToSeed,
  apiSavePost,
  apiScheduleAll,
} from '@/data/learn/learn-api'
import { canEditLearn, getLearnAuthSession } from '@/data/learn/learn-auth'
import {
  EMPTY_LEARN_STRUCTURED_POST,
  hydrateLearnStructured,
  type StructuredPost,
} from '@/data/site/structured-post'

export type LearnContentFormat = 'markdown' | 'html'

export type LearnPostMeta = {
  profiles: LearnProfileId[]
  level: LearnLevelId | ''
  tags: string[]
  excerpt: string
  durationMin: number
  prerequisites: string[]
  author: string
  authorUrl: string
  coverUrl: string
  seoTitle: string
  seoDescription: string
  seoKeywords: string[]
  canonicalUrl: string
}

export type LearnPost = LearnEpisode &
  LearnPostMeta & {
    theoryFormat: LearnContentFormat
    labFormat: LearnContentFormat
    cheatsheetFormat: LearnContentFormat
    structured: StructuredPost | null
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
  structured: StructuredPost | null
  theoryFormat: LearnContentFormat
  labFormat: LearnContentFormat
  cheatsheetFormat: LearnContentFormat
  publishedAt: string
} & LearnPostMeta

export const EMPTY_LEARN_META: LearnPostMeta = {
  profiles: [],
  level: '',
  tags: [],
  excerpt: '',
  durationMin: 0,
  prerequisites: [],
  author: '',
  authorUrl: '',
  coverUrl: '',
  seoTitle: '',
  seoDescription: '',
  seoKeywords: [],
  canonicalUrl: '',
}

export function normalizeLearnMeta(raw: Partial<LearnPostMeta> | Record<string, unknown> = {}): LearnPostMeta {
  const record = raw as Record<string, unknown>
  return {
    profiles: normalizeProfiles(record.profiles),
    level: normalizeLevel(record.level),
    tags: normalizeStringList(record.tags),
    excerpt: String(record.excerpt || '').trim(),
    durationMin: Math.max(0, Number(record.durationMin ?? record.duration_min ?? 0) || 0),
    prerequisites: normalizeStringList(record.prerequisites, 128, 24).map((s) =>
      s.toLowerCase().replace(/\s+/g, '-'),
    ),
    author: String(record.author || '').trim().slice(0, 128),
    authorUrl: String(record.authorUrl || record.author_url || '').trim().slice(0, 512),
    coverUrl: String(record.coverUrl || record.cover_url || '').trim().slice(0, 1024),
    seoTitle: String(record.seoTitle || record.seo_title || '').trim().slice(0, 200),
    seoDescription: String(record.seoDescription || record.seo_description || '')
      .trim()
      .slice(0, 400),
    seoKeywords: normalizeStringList(record.seoKeywords || record.seo_keywords),
    canonicalUrl: String(record.canonicalUrl || record.canonical_url || '')
      .trim()
      .slice(0, 512),
  }
}

function seedPublishedAt(order: number, baseMs: number): string {
  const offsetDays = Math.max(0, learnEpisodes.length - order)
  return new Date(baseMs - offsetDays * 24 * 60 * 60 * 1000).toISOString()
}

/** Offline / empty-API fallback for local UI-only work. */
export function seedPostsLocal(): LearnPost[] {
  const now = Date.now()
  const updatedAt = new Date(now).toISOString()
  return learnEpisodes.map((episode) => ({
    ...episode,
    ...normalizeLearnMeta(episode),
    theoryFormat: 'markdown' as const,
    labFormat: 'markdown' as const,
    cheatsheetFormat: 'markdown' as const,
    structured: hydrateLearnStructured(episode.structured ?? null, {
      lab: episode.lab,
      cheatsheet: episode.cheatsheet,
      cheatsheetFormat: 'markdown',
      diagram: episode.diagram,
    }),
    publishedAt: seedPublishedAt(episode.order, now),
    updatedAt,
  }))
}

export async function loadLearnPosts(opts?: { admin?: boolean }): Promise<LearnPost[]> {
  const admin = Boolean(opts?.admin && canEditLearn())
  try {
    if (admin) {
      return await apiListAdminPosts()
    }
    return await apiListPublishedPosts()
  } catch (error) {
    console.warn('Learn API unavailable, using local seed fallback', error)
    return seedPostsLocal()
  }
}

export async function getLearnPostBySlug(
  slug: string,
  opts?: { admin?: boolean; preview?: boolean },
): Promise<LearnPost | undefined> {
  const admin = Boolean(opts?.admin && canEditLearn())
  const preview = Boolean(opts?.preview && canEditLearn())
  try {
    if (admin) {
      const posts = await apiListAdminPosts()
      return posts.find((post) => post.slug === slug)
    }
    return await apiGetPublishedPost(slug, { preview })
  } catch (error) {
    console.warn('Learn API unavailable, using local seed fallback', error)
    return seedPostsLocal().find((post) => post.slug === slug)
  }
}

export async function saveLearnPost(input: LearnPostInput): Promise<LearnPost> {
  if (!getLearnAuthSession() || !canEditLearn()) {
    throw new Error('Требуется вход с ролью admin или author')
  }
  return apiSavePost(input)
}

export async function deleteLearnPost(slug: string): Promise<void> {
  if (!getLearnAuthSession() || !canEditLearn()) {
    throw new Error('Требуется вход с ролью admin или author')
  }
  await apiDeletePost(slug)
}

export async function resetLearnPostsToSeed(): Promise<LearnPost[]> {
  if (!getLearnAuthSession() || !canEditLearn()) {
    throw new Error('Требуется вход с ролью admin или author')
  }
  return apiResetToSeed()
}

export async function scheduleAllLearnPosts(
  startIso: string,
  intervalDays: number,
): Promise<LearnPost[]> {
  if (!getLearnAuthSession() || !canEditLearn()) {
    throw new Error('Требуется вход с ролью admin или author')
  }
  return apiScheduleAll(startIso, intervalDays)
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
    theory: '',
    lab: '',
    cheatsheet: '',
    diagram: '',
    links: [],
    structured: {
      ...EMPTY_LEARN_STRUCTURED_POST,
    },
    theoryFormat: 'markdown',
    labFormat: 'markdown',
    cheatsheetFormat: 'html',
    publishedAt,
    ...EMPTY_LEARN_META,
  }
}
