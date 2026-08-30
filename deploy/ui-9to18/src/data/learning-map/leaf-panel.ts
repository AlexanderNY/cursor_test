import { getMapLearnLink, normalizeMapTitle } from '@/data/learning-map/map-learn-links'
import type { MindNode } from '@/data/learning-map/parse-outline'
import type { LeafNote } from '@/data/learning-map/leaf-notes'
import type { MapCrossLink } from '@/data/learning-map/cross-links'

export type RelatedLeaf = {
  id: string
  title: string
  kind: 'cross' | 'sibling'
}

export type LeafPanelData = {
  isLeaf: boolean
  title: string
  description: string
  /** Явный ответ (заметка / outline), без автотекста. */
  customAnswer: string
  tags: string[]
  related: RelatedLeaf[]
  pathTitles: string[]
  branchTitle: string
}

function findNode(root: MindNode, id: string): MindNode | null {
  if (root.id === id) {
    return root
  }
  for (const child of root.children) {
    const found = findNode(child, id)
    if (found) {
      return found
    }
  }
  return null
}

function collectPath(root: MindNode, targetId: string): MindNode[] | null {
  if (root.id === targetId) {
    return [root]
  }
  for (const child of root.children) {
    const path = collectPath(child, targetId)
    if (path) {
      return [root, ...path]
    }
  }
  return null
}

function autoTags(title: string, path: MindNode[], branchTitle: string): string[] {
  const tags = new Set<string>()
  const branchLink = getMapLearnLink(branchTitle)
  for (const tag of branchLink?.tags || []) {
    tags.add(tag)
  }
  for (const node of path.slice(1)) {
    const short = normalizeMapTitle(node.title).split(/\s+/).slice(0, 2).join(' ')
    if (short.length >= 3 && short.length <= 24 && !short.includes('—')) {
      tags.add(short)
    }
  }
  const words = normalizeMapTitle(title)
    .replace(/[^a-zа-яё0-9\s+-]/gi, ' ')
    .split(/\s+/)
    .filter((w) => w.length >= 4)
  for (const word of words.slice(0, 4)) {
    tags.add(word)
  }
  return [...tags].slice(0, 8)
}

function defaultDescription(title: string, path: MindNode[], branchTitle: string): string {
  const branchLink = getMapLearnLink(branchTitle)
  const trail = path
    .slice(1, -1)
    .map((node) => node.title)
    .filter(Boolean)
  const place = trail.length ? trail.join(' → ') : branchTitle
  const base = branchLink?.description
    ? `${branchLink.description}`
    : `Тема из раздела «${branchTitle}».`
  if (title.length > 120) {
    return title
  }
  return `${base} Узел «${title}»${place ? ` (${place})` : ''}.`
}

export function buildLeafPanelData(
  root: MindNode,
  nodeId: string,
  crossLinks: MapCrossLink[],
  notes: Record<string, LeafNote>,
): LeafPanelData | null {
  const node = findNode(root, nodeId)
  if (!node) {
    return null
  }
  const path = collectPath(root, nodeId) || [root]
  const branch = path[1]
  const branchTitle = branch?.title || root.title
  const isLeaf = node.children.length === 0
  const note = notes[nodeId]
  const parsedTags = node.tags || []
  const tags = [
    ...new Set([
      ...(note?.tags?.length ? note.tags : []),
      ...parsedTags,
      ...(!note?.tags?.length && !parsedTags.length ? autoTags(node.title, path, branchTitle) : []),
    ]),
  ].slice(0, 12)

  const customAnswer = (note?.description || node.description || '').trim()
  const description = customAnswer || defaultDescription(node.title, path, branchTitle)

  const related: RelatedLeaf[] = []
  const seen = new Set<string>()
  for (const link of crossLinks) {
    if (link.a !== nodeId && link.b !== nodeId) {
      continue
    }
    const otherId = link.a === nodeId ? link.b : link.a
    if (seen.has(otherId)) {
      continue
    }
    const other = findNode(root, otherId)
    if (!other) {
      continue
    }
    seen.add(otherId)
    related.push({ id: otherId, title: other.title, kind: 'cross' })
  }

  const parent = path.length >= 2 ? path[path.length - 2] : null
  if (parent) {
    for (const sibling of parent.children) {
      if (sibling.id === nodeId || sibling.children.length > 0 || seen.has(sibling.id)) {
        continue
      }
      seen.add(sibling.id)
      related.push({ id: sibling.id, title: sibling.title, kind: 'sibling' })
    }
  }

  return {
    isLeaf,
    title: node.title,
    description,
    customAnswer,
    tags,
    related: related.slice(0, 24),
    pathTitles: path.map((item) => item.title),
    branchTitle,
  }
}
