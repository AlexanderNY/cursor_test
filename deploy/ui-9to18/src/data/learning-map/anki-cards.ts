import type { LearnPost } from '@/data/learn/learn-store'
import type { LeafNote } from '@/data/learning-map/leaf-notes'
import { getMapLearnLink } from '@/data/learning-map/map-learn-links'
import type { MindNode } from '@/data/learning-map/parse-outline'
import { downloadTextFile } from '@/data/learning-map/export-markdown'
import { normalizeTag } from '@/data/learning-map/tag-style'

export type AnkiLearnSource = {
  slug: string
  title: string
  episode: string
  href: string
  excerpt: string
}

export type AnkiCard = {
  id: string
  front: string
  back: string
  tags: string[]
  branch: string
  branchId: string
  path: string
  learn: AnkiLearnSource | null
}

export type CollectAnkiOptions = {
  notes?: Record<string, LeafNote>
  branchId?: string | null
  onlyLeaves?: boolean
  nodeId?: string | null
  posts?: LearnPost[]
}

function plainExcerpt(markdown: string, maxLen = 520): string {
  let text = (markdown || '')
    .replace(/\r\n/g, '\n')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*]\([^)]+\)/g, ' ')
    .replace(/\[([^\]]+)]\([^)]+\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\|\s*.+\s*\|$/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/[*_~>]+/g, ' ')
    .replace(/\n{2,}/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .trim()
  if (text.length <= maxLen) {
    return text
  }
  const cut = text.slice(0, maxLen + 1)
  const at = cut.lastIndexOf(' ')
  return `${(at > 80 ? cut.slice(0, at) : text.slice(0, maxLen)).trim()}…`
}

function scorePostForCard(card: AnkiCard, post: LearnPost): number {
  const hay = `${post.title} ${post.shortTitle} ${post.theory} ${post.cheatsheet}`.toLowerCase()
  let score = 1
  const words = card.front
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s+-]/gu, ' ')
    .split(/\s+/)
    .filter((w) => w.length >= 3)
  for (const word of words.slice(0, 8)) {
    if (hay.includes(word)) {
      score += 3
    }
  }
  for (const tag of card.tags) {
    if (hay.includes(tag.toLowerCase().replace(/_/g, ' ')) || hay.includes(tag.toLowerCase())) {
      score += 2
    }
  }
  if (post.cheatsheet?.trim()) {
    score += 1
  }
  return score
}

export function buildLearnSource(card: AnkiCard, posts: LearnPost[]): AnkiLearnSource | null {
  const link = getMapLearnLink(card.branch)
  if (!link || link.episodeSlugs.length === 0 || posts.length === 0) {
    return null
  }
  const bySlug = new Map(posts.map((post) => [post.slug, post]))
  const candidates = link.episodeSlugs
    .map((slug) => bySlug.get(slug))
    .filter((post): post is LearnPost => Boolean(post))
  if (candidates.length === 0) {
    return null
  }
  let best = candidates[0]
  let bestScore = -1
  for (const post of candidates) {
    const score = scorePostForCard(card, post)
    if (score > bestScore) {
      best = post
      bestScore = score
    }
  }
  const excerptSource = best.cheatsheet?.trim() || best.theory || ''
  const excerpt = plainExcerpt(excerptSource)
  if (!excerpt) {
    return null
  }
  return {
    slug: best.slug,
    title: best.shortTitle || best.title,
    episode: best.episode,
    href: `/game/learn/${best.slug}`,
    excerpt,
  }
}

export function attachLearnSources(cards: AnkiCard[], posts: LearnPost[]): AnkiCard[] {
  if (!posts.length) {
    return cards.map((card) => ({ ...card, learn: card.learn ?? null }))
  }
  return cards.map((card) => ({
    ...card,
    learn: buildLearnSource(card, posts),
  }))
}

function walk(
  node: MindNode,
  path: MindNode[],
  notes: Record<string, LeafNote>,
  onlyLeaves: boolean,
  nodeId: string | null | undefined,
  out: AnkiCard[],
): void {
  const nextPath = [...path, node]
  const isLeaf = node.children.length === 0
  const matchId = !nodeId || node.id === nodeId
  const includeNode = matchId && (!onlyLeaves || isLeaf) && node.id !== 'root'

  if (includeNode) {
    const note = notes[node.id]
    const back = (note?.description || node.description || '').trim()
    if (back) {
      const branchNode = nextPath[1]
      const branch = branchNode?.title || nextPath[0]?.title || ''
      const branchId = branchNode?.id || ''
      const link = getMapLearnLink(branch)
      const tags = [
        ...new Set([
          ...(note?.tags || []),
          ...(node.tags || []),
          ...(link?.tags || []),
          ...(branch ? [normalizeTag(branch)] : []),
        ]),
      ]
        .map((tag) => normalizeTag(tag))
        .filter(Boolean)
        .slice(0, 12)

      out.push({
        id: node.id,
        front: node.title.trim() || '—',
        back,
        tags,
        branch,
        branchId,
        path: nextPath
          .slice(1)
          .map((item) => item.title)
          .join(' → '),
        learn: null,
      })
    }
  }

  if (nodeId && node.id === nodeId) {
    return
  }

  for (const child of node.children) {
    walk(child, nextPath, notes, onlyLeaves, nodeId, out)
  }
}

/** Собирает Anki-карты: лицевая = тема, оборот = краткий ответ. */
export function collectAnkiCards(root: MindNode, options: CollectAnkiOptions = {}): AnkiCard[] {
  const notes = options.notes || {}
  const onlyLeaves = options.onlyLeaves !== false
  const nodeId = options.nodeId || null
  const out: AnkiCard[] = []

  let start = root
  if (options.branchId) {
    const branch = root.children.find((child) => child.id === options.branchId)
    if (!branch) {
      return []
    }
    start = { ...root, children: [branch] }
  }

  walk(start, [], notes, onlyLeaves, nodeId, out)
  const cards = options.posts?.length ? attachLearnSources(out, options.posts) : out
  return cards
}

export function filterAnkiCards(
  cards: AnkiCard[],
  opts: { branchIds?: string[]; tags?: string[] },
): AnkiCard[] {
  const branchIds = new Set((opts.branchIds || []).filter(Boolean))
  const tags = new Set((opts.tags || []).map((tag) => normalizeTag(tag)).filter(Boolean))
  return cards.filter((card) => {
    if (branchIds.size > 0 && !branchIds.has(card.branchId)) {
      return false
    }
    if (tags.size > 0 && !card.tags.some((tag) => tags.has(normalizeTag(tag)))) {
      return false
    }
    return true
  })
}

function escapeTsvCell(value: string): string {
  return value.replace(/\r?\n/g, '<br>').replace(/\t/g, ' ')
}

function learnAbsoluteHref(href: string): string {
  if (/^https?:\/\//i.test(href)) {
    return href
  }
  if (typeof window !== 'undefined' && window.location?.origin) {
    return `${window.location.origin}${href.startsWith('/') ? '' : '/'}${href}`
  }
  return href
}

function formatBackHtml(card: AnkiCard): string {
  const parts = [`<div>${escapeTsvCell(card.back)}</div>`]
  if (card.learn?.excerpt) {
    parts.push(
      `<hr><div><b>Конспект Learn</b> (${escapeTsvCell(card.learn.episode)} · ${escapeTsvCell(card.learn.title)})</div>`,
      `<div>${escapeTsvCell(card.learn.excerpt)}</div>`,
    )
  }
  if (card.learn?.href) {
    const href = learnAbsoluteHref(card.learn.href)
    parts.push(
      `<div><a href="${escapeTsvCell(href)}">Статья Learn: ${escapeTsvCell(card.learn.title)}</a></div>`,
    )
  }
  return parts.join('<br>')
}

/** TSV для File → Import в Anki (Tab, поля Front / Back / Tags). */
export function serializeAnkiTsv(cards: AnkiCard[], deckName = '9to18::собеседование'): string {
  const lines = [
    '#separator:Tab',
    '#html:true',
    `#deck:${deckName}`,
    '#notetype:Basic',
    '#columns:Front\tBack\tTags',
    '#tags column:3',
  ]
  for (const card of cards) {
    const tags = card.tags.join(' ')
    lines.push(`${escapeTsvCell(card.front)}\t${formatBackHtml(card)}\t${escapeTsvCell(tags)}`)
  }
  return `${lines.join('\n')}\n`
}

export function suggestAnkiFilename(prefix = 'anki-9to18'): string {
  const date = new Date().toISOString().slice(0, 10)
  return `${prefix}-${date}.txt`
}

export function downloadAnkiDeck(cards: AnkiCard[], filename?: string): void {
  if (cards.length === 0) {
    return
  }
  downloadTextFile(filename || suggestAnkiFilename(), serializeAnkiTsv(cards), 'text/plain;charset=utf-8')
}

export function downloadSingleAnkiCard(card: AnkiCard): void {
  const safe = card.front
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
  downloadAnkiDeck([card], suggestAnkiFilename(safe || 'anki-card'))
}
