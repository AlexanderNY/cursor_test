import type { LearnPost } from '@/data/learn/learn-store'
import type { LeafNote } from '@/data/learning-map/leaf-notes'
import type { MindNode } from '@/data/learning-map/parse-outline'
import { downloadTextFile } from '@/data/learning-map/export-markdown'
import { normalizeTag } from '@/data/learning-map/tag-style'
import { learnAnkiCards } from '@/data/site/structured-post'

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

function learnSourceFromPost(post: LearnPost): AnkiLearnSource {
  const excerptSource =
    post.structured?.intro ||
    post.cheatsheet?.trim() ||
    post.theory ||
    post.title
  return {
    slug: post.slug,
    title: post.shortTitle || post.title,
    episode: post.episode,
    href: `/game/learn/${post.slug}`,
    excerpt: plainExcerpt(excerptSource),
  }
}

function walk(
  node: MindNode,
  path: MindNode[],
  notes: Record<string, LeafNote>,
  onlyLeaves: boolean,
  nodeId: string | null | undefined,
  postsBySlug: Map<string, LearnPost>,
  out: AnkiCard[],
): void {
  const nextPath = [...path, node]
  const isLeaf = node.children.length === 0
  const matchId = !nodeId || node.id === nodeId
  const includeNode = matchId && (!onlyLeaves || isLeaf) && node.id !== 'root'

  if (includeNode) {
    const branchNode = nextPath[1]
    const branch = branchNode?.title || nextPath[0]?.title || ''
    const branchId = branchNode?.id || ''
    const pathLabel = nextPath
      .slice(1)
      .map((item) => item.title)
      .join(' → ')
    const note = notes[node.id]
    const post = node.learnSlug ? postsBySlug.get(node.learnSlug) : undefined

    if (post?.structured) {
      const cards = learnAnkiCards(post.structured)
      cards.forEach((card, index) => {
        out.push({
          id: `learn:${post.slug}:${index}:${card.front.slice(0, 40)}`,
          front: card.front.trim() || node.title,
          back: card.back.trim(),
          tags: [
            ...new Set([
              ...(note?.tags || []),
              ...(node.tags || []),
              ...(branch ? [normalizeTag(branch)] : []),
              'learn',
              post.slug,
            ]),
          ]
            .map((tag) => normalizeTag(tag))
            .filter(Boolean)
            .slice(0, 12),
          branch,
          branchId,
          path: pathLabel,
          learn: learnSourceFromPost(post),
        })
      })
    } else {
      const back = (note?.description || node.description || post?.theory || '').trim()
      if (back) {
        out.push({
          id: node.id,
          front: node.title.trim() || '—',
          back,
          tags: [
            ...new Set([
              ...(note?.tags || []),
              ...(node.tags || []),
              ...(branch ? [normalizeTag(branch)] : []),
            ]),
          ]
            .map((tag) => normalizeTag(tag))
            .filter(Boolean)
            .slice(0, 12),
          branch,
          branchId,
          path: pathLabel,
          learn: post ? learnSourceFromPost(post) : null,
        })
      }
    }
  }

  if (nodeId && node.id === nodeId) {
    return
  }

  for (const child of node.children) {
    walk(child, nextPath, notes, onlyLeaves, nodeId, postsBySlug, out)
  }
}

/** Колода Anki: карточки из Learn-статей, привязанных к листьям карты. */
export function collectAnkiCards(root: MindNode, options: CollectAnkiOptions = {}): AnkiCard[] {
  const notes = options.notes || {}
  const onlyLeaves = options.onlyLeaves !== false
  const nodeId = options.nodeId || null
  const out: AnkiCard[] = []
  const postsBySlug = new Map((options.posts || []).map((post) => [post.slug, post]))

  let start = root
  if (options.branchId) {
    const branch = root.children.find((child) => child.id === options.branchId)
    if (!branch) {
      return []
    }
    start = { ...root, children: [branch] }
  }

  walk(start, [], notes, onlyLeaves, nodeId, postsBySlug, out)
  return out
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
