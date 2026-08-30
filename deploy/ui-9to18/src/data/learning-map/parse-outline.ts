export type MindNode = {
  id: string
  title: string
  children: MindNode[]
  description?: string
  tags?: string[]
}

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
  // outline export: depth 3 = `- `, deeper = 2 spaces per level
  return 3 + Math.floor(spaces / 2)
}

function cleanTitle(raw: string): string {
  return raw.replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim()
}

function extractTags(raw: string): { text: string; tags: string[] } {
  const tags: string[] = []
  const text = raw
    .replace(/(^|\s)#([A-Za-zА-Яа-яЁё0-9_+-]+)/g, (_full, space: string, tag: string) => {
      tags.push(tag.toLowerCase())
      return space
    })
    .replace(/\s+/g, ' ')
    .trim()
  return { text, tags }
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
    const tagged = extractTags(rawTitle)
    const split = splitTitleDescription(tagged.text)
    const node: MindNode = {
      id: `n${counter}`,
      title: split.title || '—',
      children: [],
      description: split.description || undefined,
      tags: tagged.tags.length ? tagged.tags : undefined,
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
        root.title = title || root.title
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
  return root
}

export function countNodes(node: MindNode): number {
  return 1 + node.children.reduce((sum, child) => sum + countNodes(child), 0)
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
    (node.tags || []).some((tag) => tag.toLowerCase().includes(q))
  if (!selfMatch && filteredChildren.length === 0) {
    return null
  }
  return {
    ...node,
    children: selfMatch && filteredChildren.length === 0 ? node.children : filteredChildren,
  }
}

type TagLookup = (node: MindNode) => string[]

/** Оставляет узлы, у которых есть любой из selectedTags (или потомок с таким тегом). */
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

/** Обрезает дерево до maxDepth уровней от корня (корень = уровень 0). */
export function limitDepth(node: MindNode, maxDepth: number, depth = 0): MindNode {
  if (depth >= maxDepth) {
    return { ...node, children: [] }
  }
  return {
    ...node,
    children: node.children.map((child) => limitDepth(child, maxDepth, depth + 1)),
  }
}
