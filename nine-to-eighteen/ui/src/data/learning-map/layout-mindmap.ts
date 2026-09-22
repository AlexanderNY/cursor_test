import type { MindNode } from '@/data/learning-map/parse-outline'

export type LayoutNode = {
  id: string
  title: string
  titleLines: string[]
  fullTitle: string
  description: string
  depth: number
  x: number
  y: number
  width: number
  height: number
  side: -1 | 0 | 1
  childCount: number
  hasHiddenChildren: boolean
}

export type LayoutEdge = {
  id: string
  parentId: string
  childId: string
  d: string
}

export type MindLayout = {
  nodes: LayoutNode[]
  edges: LayoutEdge[]
  width: number
  height: number
  originX: number
  originY: number
}

const LEVEL_GAP = 200
const NODE_GAP = 8

/** Делит подпись узла максимум на 2 строки по словам. */
function wrapTwoLines(title: string, maxPerLine: number): string[] {
  const clean = title.replace(/\s+/g, ' ').trim()
  if (!clean) {
    return ['—']
  }
  const maxTotal = maxPerLine * 2
  const text =
    clean.length > maxTotal ? `${clean.slice(0, Math.max(1, maxTotal - 1))}…` : clean
  if (text.length <= maxPerLine) {
    return [text]
  }

  const ideal = Math.ceil(text.length / 2)
  let breakAt = text.lastIndexOf(' ', ideal)
  if (breakAt < Math.floor(maxPerLine * 0.35)) {
    const forward = text.indexOf(' ', ideal)
    breakAt = forward > 0 ? forward : breakAt
  }
  if (breakAt <= 0) {
    breakAt = Math.min(maxPerLine, text.length)
    const first = text.slice(0, breakAt).trim()
    const second = text.slice(breakAt).trim()
    return second ? [first, second] : [first]
  }

  const first = text.slice(0, breakAt).trim()
  let second = text.slice(breakAt).trim()
  if (second.length > maxPerLine) {
    second = `${second.slice(0, Math.max(1, maxPerLine - 1))}…`
  }
  return second ? [first, second] : [first]
}

function measure(
  title: string,
  depth: number,
): { width: number; height: number; label: string; lines: string[] } {
  const maxChars = depth === 0 ? 18 : depth === 1 ? 16 : depth === 2 ? 14 : 12
  const lines = wrapTwoLines(title, maxChars)
  const label = lines.join(' ')
  const longest = Math.max(...lines.map((line) => line.length), 1)
  const lineCount = lines.length

  if (depth === 0) {
    return {
      width: Math.min(200, Math.max(150, 20 + longest * 7.2)),
      height: lineCount > 1 ? 64 : 58,
      label,
      lines,
    }
  }
  if (depth === 1) {
    return {
      width: Math.min(200, Math.max(118, 16 + longest * 7)),
      height: lineCount > 1 ? 50 : 42,
      label,
      lines,
    }
  }
  return {
    width: Math.min(176, Math.max(104, 14 + longest * 6.4)),
    height: lineCount > 1 ? 42 : 32,
    label,
    lines,
  }
}

function leafWeight(node: MindNode, depth: number, maxDepth: number): number {
  if (depth >= maxDepth || node.children.length === 0) {
    return 1
  }
  return Math.max(
    1,
    node.children.reduce((sum, child) => sum + leafWeight(child, depth + 1, maxDepth), 0),
  )
}

function linkPath(x1: number, y1: number, x2: number, y2: number, side: -1 | 1): string {
  const dx = Math.max(36, Math.abs(x2 - x1) * 0.42)
  return `M ${x1} ${y1} C ${x1 + side * dx} ${y1}, ${x2 - side * dx} ${y2}, ${x2} ${y2}`
}

type Accum = {
  nodes: LayoutNode[]
  edges: LayoutEdge[]
}

function layoutChildren(
  children: MindNode[],
  side: -1 | 1,
  depth: number,
  maxDepth: number,
  parent: LayoutNode,
  topY: number,
  acc: Accum,
): number {
  if (children.length === 0 || depth > maxDepth) {
    return 0
  }

  const weights = children.map((child) => leafWeight(child, depth, maxDepth))
  const unit = 36
  const spans = weights.map((w) => Math.max(unit, w * unit))
  const totalSpan =
    spans.reduce((a, b) => a + b, 0) + NODE_GAP * Math.max(0, children.length - 1)

  let y = topY
  children.forEach((child, index) => {
    const span = spans[index]
    const centerY = y + span / 2
    const size = measure(child.title, depth)
    const x = parent.x + side * (parent.width / 2 + LEVEL_GAP * 0.55 + size.width / 2)

    const layoutNode: LayoutNode = {
      id: child.id,
      title: size.label,
      titleLines: size.lines,
      fullTitle: child.title,
      description: child.description || '',
      depth,
      x,
      y: centerY,
      width: size.width,
      height: size.height,
      side,
      childCount: child.children.length,
      hasHiddenChildren: depth >= maxDepth && child.children.length > 0,
    }
    acc.nodes.push(layoutNode)

    const x1 = parent.x + side * (parent.width / 2)
    const x2 = x - side * (size.width / 2)
    acc.edges.push({
      id: `${parent.id}->${child.id}`,
      parentId: parent.id,
      childId: child.id,
      d: linkPath(x1, parent.y, x2, centerY, side),
    })

    if (depth < maxDepth && child.children.length > 0) {
      const childSpan = Math.max(span, child.children.length * unit)
      layoutChildren(
        child.children,
        side,
        depth + 1,
        maxDepth,
        layoutNode,
        centerY - childSpan / 2,
        acc,
      )
    }

    y += span + NODE_GAP
  })

  return totalSpan
}

/** Классическая mind map: корень в центре, ветки влево и вправо. */
export function layoutMindmap(root: MindNode, maxDepth: number): MindLayout {
  const rootSize = measure(root.title, 0)
  const rootNode: LayoutNode = {
    id: root.id,
    title: rootSize.label,
    titleLines: rootSize.lines,
    fullTitle: root.title,
    description: root.description || '',
    depth: 0,
    x: 0,
    y: 0,
    width: rootSize.width,
    height: rootSize.height,
    side: 0,
    childCount: root.children.length,
    hasHiddenChildren: maxDepth < 1 && root.children.length > 0,
  }

  const acc: Accum = { nodes: [rootNode], edges: [] }

  if (maxDepth >= 1 && root.children.length > 0) {
    const mid = Math.ceil(root.children.length / 2)
    const left = root.children.slice(0, mid)
    const right = root.children.slice(mid)

    const leftWeights = left.map((n) => leafWeight(n, 1, maxDepth))
    const rightWeights = right.map((n) => leafWeight(n, 1, maxDepth))
    const leftSpan =
      leftWeights.reduce((a, b) => a + Math.max(36, b * 36), 0) +
      NODE_GAP * Math.max(0, left.length - 1)
    const rightSpan =
      rightWeights.reduce((a, b) => a + Math.max(36, b * 36), 0) +
      NODE_GAP * Math.max(0, right.length - 1)

    layoutChildren(left, -1, 1, maxDepth, rootNode, -leftSpan / 2, acc)
    layoutChildren(right, 1, 1, maxDepth, rootNode, -rightSpan / 2, acc)
  }

  let minX = Infinity
  let maxX = -Infinity
  let minY = Infinity
  let maxY = -Infinity
  for (const node of acc.nodes) {
    minX = Math.min(minX, node.x - node.width / 2)
    maxX = Math.max(maxX, node.x + node.width / 2)
    minY = Math.min(minY, node.y - node.height / 2)
    maxY = Math.max(maxY, node.y + node.height / 2)
  }

  const pad = 56
  return {
    nodes: acc.nodes,
    edges: acc.edges,
    width: Math.max(400, maxX - minX + pad * 2),
    height: Math.max(280, maxY - minY + pad * 2),
    originX: -minX + pad,
    originY: -minY + pad,
  }
}
