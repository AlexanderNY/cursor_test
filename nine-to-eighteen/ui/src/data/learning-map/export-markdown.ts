import type { MapCrossLink } from '@/data/learning-map/cross-links'
import type { LeafNote } from '@/data/learning-map/leaf-notes'
import type { MindNode } from '@/data/learning-map/parse-outline'

export type ExportMarkdownOptions = {
  notes?: Record<string, LeafNote>
  crossLinks?: MapCrossLink[]
  /** If set, only these L1 branch ids are exported (others skipped). Empty = all. */
  includeBranchIds?: string[] | null
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

function mergeNotes(node: MindNode, notes: Record<string, LeafNote>): MindNode {
  const note = notes[node.id]
  const description = (note?.description?.trim() || node.description || '').trim()
  const tags = [...new Set([...(node.tags || []), ...(note?.tags || [])])]
  return {
    ...node,
    description: description || undefined,
    tags: tags.length ? tags : undefined,
    children: node.children.map((child) => mergeNotes(child, notes)),
  }
}

function formatLineTitle(node: MindNode): string {
  let text = node.title.trim() || '—'
  const description = (node.description || '').trim()
  if (description) {
    text = `${text} — ${description}`
  }
  for (const tag of node.tags || []) {
    const safe = tag.trim().replace(/\s+/g, '_')
    if (safe) {
      text += ` #${safe}`
    }
  }
  return text
}

function serializeTree(root: MindNode): string {
  const lines: string[] = []

  const walk = (node: MindNode, depth: number): void => {
    if (depth === 0) {
      lines.push(`# ${node.title.trim() || 'карта'}`)
      lines.push('')
      for (const child of node.children) {
        walk(child, 1)
      }
      return
    }

    if (depth === 1) {
      lines.push(`## ${formatLineTitle(node)}`)
      for (const child of node.children) {
        walk(child, 2)
      }
      lines.push('')
      return
    }

    if (depth === 2) {
      lines.push(`### ${formatLineTitle(node)}`)
      for (const child of node.children) {
        walk(child, 3)
      }
      return
    }

    const indent = '  '.repeat(depth - 3)
    lines.push(`${indent}- ${formatLineTitle(node)}`)
    for (const child of node.children) {
      walk(child, depth + 1)
    }
  }

  walk(root, 0)
  return lines.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n'
}

function wikiHeading(title: string): string {
  const clean = title.trim().replace(/[\[\]]/g, '')
  return `[[#${clean}]]`
}

function buildCrossLinksBlock(root: MindNode, links: MapCrossLink[]): string {
  if (links.length === 0) {
    return ''
  }
  const rows: string[] = []
  for (const link of links) {
    const left = findNode(root, link.a)
    const right = findNode(root, link.b)
    if (!left || !right) {
      continue
    }
    rows.push(`- ${wikiHeading(left.title)} ↔ ${wikiHeading(right.title)}`)
  }
  if (rows.length === 0) {
    return ''
  }
  return [
    '',
    '%%',
    'Связи между листьями (Obsidian wikilinks; блок скрыт в режиме чтения).',
    'Импорт обратно в 9to18 этот блок не разбирает.',
    ...rows,
    '%%',
    '',
  ].join('\n')
}

function buildFrontmatter(root: MindNode): string {
  const date = new Date().toISOString().slice(0, 10)
  const title = root.title.trim().replace(/"/g, '\\"')
  return [
    '---',
    `title: "${title}"`,
    'tags:',
    '  - learning-map',
    '  - interview-prep',
    '  - 9to18',
    `exported: ${date}`,
    'source: 9to18.ru',
    '---',
    '',
  ].join('\n')
}

/** Собирает Markdown outline (совместим с парсером карты) + мета для Obsidian. */
export function buildLearningMapMarkdown(
  root: MindNode,
  options: ExportMarkdownOptions = {},
): string {
  const notes = options.notes || {}
  let tree = mergeNotes(root, notes)

  if (options.includeBranchIds && options.includeBranchIds.length > 0) {
    const allow = new Set(options.includeBranchIds)
    tree = {
      ...tree,
      children: tree.children.filter((branch) => allow.has(branch.id)),
    }
  }

  const body = serializeTree(tree)
  const linksBlock = buildCrossLinksBlock(tree, options.crossLinks || [])
  return `${buildFrontmatter(tree)}${body}${linksBlock}`
}

export function suggestExportFilename(root: MindNode): string {
  const base = root.title
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48)
  const date = new Date().toISOString().slice(0, 10)
  return `${base || 'learning-map'}-${date}.md`
}

export function downloadMarkdownFile(filename: string, content: string): void {
  downloadTextFile(filename, content, 'text/markdown;charset=utf-8')
}

export function downloadTextFile(
  filename: string,
  content: string,
  mime = 'text/plain;charset=utf-8',
): void {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
