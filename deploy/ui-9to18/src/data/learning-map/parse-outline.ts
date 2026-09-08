export type MindNode = {
  id: string
  title: string
  children: MindNode[]
  description?: string
  tags?: string[]
  /** Learn article slug when leaf is linked 1:1. */
  learnSlug?: string
  /** Profile ids that should see this node (empty = all). */
  profiles?: string[]
}

export const LEARN_MAP_PROFILES = [
  { id: 'analyst', label: 'Аналитик' },
  { id: 'devops', label: 'DevOps' },
  { id: 'developer', label: 'Разработчик' },
  { id: 'tester', label: 'Тестировщик' },
  { id: 'product_owner', label: 'Владелец продукта' },
] as const

export type LearnMapProfileId = (typeof LEARN_MAP_PROFILES)[number]['id']

type StackItem = { depth: number; node: MindNode }

function headingDepth(line: string): number | null {
  const match = /^(#{1,6})\s+(.+)$/.exec(line)
  if (!match) {
    return null
  }
  return match[1].length
}

function bulletDepth(line: string): number | null {
  const match = /^(\s*)-\s+(.+)$/.exec(line)
  if (!match) {
    return null
  }
  const spaces = match[1].replace(/\t/g, '  ').length
  return 3 + Math.floor(spaces / 2)
}

function cleanTitle(raw: string): string {
  return raw.replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim()
}

function extractMeta(raw: string): {
  text: string
  tags: string[]
  learnSlug?: string
  profiles?: string[]
} {
  let text = cleanTitle(raw)
  let learnSlug: string | undefined
  let profiles: string[] | undefined
  const brace = /\{([^}]*)\}\s*$/.exec(text)
  if (brace) {
    const meta = brace[1]
    text = text.slice(0, brace.index).trim()
    const learnMatch = /learn\s*:\s*([a-z0-9-]+)/i.exec(meta)
    if (learnMatch) {
      learnSlug = learnMatch[1].toLowerCase()
    }
    const profilesMatch = /profiles\s*:\s*([a-z0-9_,\s-]+)/i.exec(meta)
    if (profilesMatch) {
      profiles = profilesMatch[1]
        .split(/[,|\s]+/)
        .map((p) => p.trim().toLowerCase())
        .filter(Boolean)
    }
  }
  const tags: string[] = []
  text = text
    .replace(/(^|\s)#([A-Za-zА-Яа-яЁё0-9_+-]+)/g, (_full, space: string, tag: string) => {
      tags.push(tag.toLowerCase())
      return space
    })
    .replace(/\s+/g, ' ')
    .trim()
  return { text, tags, learnSlug, profiles }
}

function splitTitleDescription(raw: string): { title: string; description: string } {
  const cleaned = cleanTitle(raw)
  const emDash = cleaned.indexOf(' — ')
  if (emDash > 0 && cleaned.length - emDash > 40) {
    return {
      title: cleaned.slice(0, emDash).trim(),
      description: cleaned.slice(emDash + 3).trim(),
    }
  }
  const slash = cleaned.indexOf(' / ')
  if (slash > 0 && cleaned.length - slash > 40) {
    return {
      title: cleaned.slice(0, slash).trim(),
      description: cleaned.slice(slash + 3).trim(),
    }
  }
  return { title: cleaned, description: '' }
}

/** Убирает YAML frontmatter и %%…%% (экспорт Obsidian / админка). */
export function stripOutlineMeta(markdown: string): string {
  let text = markdown.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n')
  if (text.startsWith('---')) {
    const end = text.indexOf('\n---', 3)
    if (end !== -1) {
      text = text.slice(end + 4).replace(/^\n+/, '')
    }
  }
  text = text.replace(/%%[\s\S]*?%%/g, '\n')
  return text.trim() + (text.trim() ? '\n' : '')
}

/** Если у узла ровно один длинный дочерний лист — это описание, а не отдельная тема. */
function promoteDescriptionChildren(node: MindNode): void {
  for (const child of node.children) {
    promoteDescriptionChildren(child)
  }
  if (node.children.length !== 1) {
    return
  }
  const only = node.children[0]
  if (only.children.length > 0) {
    return
  }
  if (only.title.length < 80 || node.title.length > 70) {
    return
  }
  if (!node.description) {
    node.description = only.title
  }
  node.tags = [...new Set([...(node.tags || []), ...(only.tags || [])])]
  if (!node.learnSlug && only.learnSlug) {
    node.learnSlug = only.learnSlug
  }
  if ((!node.profiles || node.profiles.length === 0) && only.profiles?.length) {
    node.profiles = only.profiles
  }
  node.children = []
}

/** Парсит outline из `#` / `##` / `###` / `-` в дерево mind map. */
export function parseOutlineMarkdown(markdown: string): MindNode {
  const root: MindNode = { id: 'root', title: 'собеседование', children: [] }
  const stack: StackItem[] = [{ depth: 0, node: root }]
  let counter = 0

  const pushNode = (depth: number, rawTitle: string): void => {
    while (stack.length > 1 && stack[stack.length - 1].depth >= depth) {
      stack.pop()
    }
    const parent = stack[stack.length - 1].node
    counter += 1
    const meta = extractMeta(rawTitle)
    const split = splitTitleDescription(meta.text)
    const node: MindNode = {
      id: `n${counter}`,
      title: split.title || '—',
      children: [],
      description: split.description || undefined,
      tags: meta.tags.length ? meta.tags : undefined,
      learnSlug: meta.learnSlug,
      profiles: meta.profiles,
    }
    parent.children.push(node)
    stack.push({ depth, node })
  }

  for (const rawLine of stripOutlineMeta(markdown).split('\n')) {
    const line = rawLine.replace(/\s+$/, '')
    if (!line.trim()) {
      continue
    }

    const hDepth = headingDepth(line)
    if (hDepth !== null) {
      const title = cleanTitle(line.replace(/^#{1,6}\s+/, ''))
      if (hDepth === 1) {
        root.title = extractMeta(title).text || root.title
        stack.length = 1
        continue
      }
      pushNode(hDepth, title)
      continue
    }

    const bDepth = bulletDepth(line)
    if (bDepth !== null) {
      const title = cleanTitle(line.replace(/^\s*-\s+/, ''))
      pushNode(bDepth, title)
    }
  }

  promoteDescriptionChildren(root)
  enforceLearnSlugLeafInvariant(root)
  return root
}

/**
 * Invariant: one Learn article (learnSlug) ↔ one leaf node.
 * - learnSlug only kept on leaves (no children).
 * - duplicate slug on a later node is dropped (console warn).
 */
export function enforceLearnSlugLeafInvariant(root: MindNode): void {
  const seen = new Map<string, string>()

  const walk = (node: MindNode): void => {
    for (const child of node.children) {
      walk(child)
    }
    if (!node.learnSlug) {
      return
    }
    const slug = node.learnSlug.toLowerCase()
    const isLeaf = node.children.length === 0 && node.id !== 'root'
    if (!isLeaf) {
      if (typeof console !== 'undefined') {
        console.warn(
          `[learning-map] learn:${slug} ignored on non-leaf «${node.title}» (id=${node.id})`,
        )
      }
      delete node.learnSlug
      return
    }
    const prevId = seen.get(slug)
    if (prevId) {
      if (typeof console !== 'undefined') {
        console.warn(
          `[learning-map] duplicate learn:${slug} on «${node.title}» (id=${node.id}); kept ${prevId}`,
        )
      }
      delete node.learnSlug
      return
    }
    seen.set(slug, node.id)
  }

  walk(root)
}

export function countNodes(node: MindNode): number {
  return 1 + node.children.reduce((sum, child) => sum + countNodes(child), 0)
}

export function collectLeaves(node: MindNode, acc: MindNode[] = []): MindNode[] {
  if (node.children.length === 0 && node.id !== 'root') {
    acc.push(node)
    return acc
  }
  for (const child of node.children) {
    collectLeaves(child, acc)
  }
  return acc
}

export function filterTree(node: MindNode, query: string): MindNode | null {
  const q = query.trim().toLowerCase()
  if (!q) {
    return node
  }
  const filteredChildren = node.children
    .map((child) => filterTree(child, q))
    .filter((child): child is MindNode => child !== null)
  const selfMatch =
    node.title.toLowerCase().includes(q) ||
    (node.description || '').toLowerCase().includes(q) ||
    (node.tags || []).some((tag) => tag.toLowerCase().includes(q)) ||
    (node.learnSlug || '').toLowerCase().includes(q)
  if (!selfMatch && filteredChildren.length === 0) {
    return null
  }
  return {
    ...node,
    children: selfMatch && filteredChildren.length === 0 ? node.children : filteredChildren,
  }
}

type TagLookup = (node: MindNode) => string[]

export function filterTreeByTags(
  node: MindNode,
  selectedTags: string[],
  getTags: TagLookup,
): MindNode | null {
  const wanted = new Set(
    selectedTags.map((tag) => tag.trim().toLowerCase()).filter(Boolean),
  )
  if (wanted.size === 0) {
    return node
  }

  const filteredChildren = node.children
    .map((child) => filterTreeByTags(child, selectedTags, getTags))
    .filter((child): child is MindNode => child !== null)

  const selfMatch = getTags(node).some((tag) => wanted.has(tag.trim().toLowerCase()))
  if (!selfMatch && filteredChildren.length === 0) {
    return null
  }
  return {
    ...node,
    children: filteredChildren,
  }
}

/** Filter by career profile: keep branch if it or a descendant matches. */
export function filterTreeByProfile(
  node: MindNode,
  profileId: string | null,
): MindNode | null {
  if (!profileId) {
    return node
  }
  const wanted = profileId.trim().toLowerCase()
  const filteredChildren = node.children
    .map((child) => filterTreeByProfile(child, profileId))
    .filter((child): child is MindNode => child !== null)

  if (node.children.length > 0) {
    if (filteredChildren.length === 0) {
      return null
    }
    return { ...node, children: filteredChildren }
  }
  const selfProfiles = (node.profiles || []).map((p) => p.toLowerCase())
  const selfMatch = selfProfiles.length === 0 || selfProfiles.includes(wanted)
  if (!selfMatch) {
    return null
  }
  return { ...node, children: [] }
}

export function limitDepth(node: MindNode, maxDepth: number, depth = 0): MindNode {
  if (depth >= maxDepth) {
    return { ...node, children: [] }
  }
  return {
    ...node,
    children: node.children.map((child) => limitDepth(child, maxDepth, depth + 1)),
  }
}
