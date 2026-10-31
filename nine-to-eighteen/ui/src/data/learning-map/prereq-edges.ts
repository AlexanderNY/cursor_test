import type { LayoutNode } from '@/data/learning-map/layout-mindmap'
import type { MindNode } from '@/data/learning-map/parse-outline'

export type PrereqArrow = {
  id: string
  fromId: string
  toId: string
  fromTitle: string
  toTitle: string
  d: string
}

function indexLearnNodes(root: MindNode): Map<string, MindNode> {
  const bySlug = new Map<string, MindNode>()
  const walk = (node: MindNode): void => {
    const slug = (node.learnSlug || '').trim().toLowerCase()
    if (slug && !bySlug.has(slug)) {
      bySlug.set(slug, node)
    }
    for (const child of node.children) {
      walk(child)
    }
  }
  walk(root)
  return bySlug
}

function arrowPath(from: LayoutNode, to: LayoutNode, slot: number, slots: number): string {
  const spread = (slot - (slots - 1) / 2) * 14
  const dirX = Math.sign(to.x - from.x) || 1
  const x1 = from.x + dirX * (from.width / 2)
  const y1 = from.y
  const x2 = to.x - dirX * (to.width / 2)
  const y2 = to.y + spread
  const midX = (x1 + x2) / 2
  const bow = (y1 <= y2 ? -1 : 1) * (36 + Math.abs(slot) * 8)
  const midY = (y1 + y2) / 2 + bow
  return `M ${x1} ${y1} Q ${midX} ${midY}, ${x2} ${y2}`
}

export function linkedByPrereq(
  root: MindNode,
  node: MindNode,
): { before: Array<{ slug: string; node: MindNode | null }>; after: MindNode[] } {
  const bySlug = indexLearnNodes(root)
  const before = (node.prerequisites || []).map((slug) => {
    const key = slug.trim().toLowerCase()
    return { slug: key, node: bySlug.get(key) || null }
  })
  const own = (node.learnSlug || '').trim().toLowerCase()
  const after: MindNode[] = []
  if (own) {
    const walk = (current: MindNode): void => {
      if (current.id !== node.id && current.prerequisites?.some((slug) => slug.toLowerCase() === own)) {
        after.push(current)
      }
      for (const child of current.children) {
        walk(child)
      }
    }
    walk(root)
  }
  return { before, after }
}

/** Стрелка из каждой статьи-пререквизита в ту, которую читают после неё. */
export function buildPrereqArrows(root: MindNode, layoutNodes: LayoutNode[]): PrereqArrow[] {
  const bySlug = indexLearnNodes(root)
  const placed = new Map(layoutNodes.map((node) => [node.id, node]))
  const pending: Array<{ from: MindNode; to: MindNode }> = []

  const walk = (node: MindNode): void => {
    const target = placed.get(node.id)
    if (target && node.prerequisites?.length) {
      for (const slug of node.prerequisites) {
        const source = bySlug.get(slug.trim().toLowerCase())
        if (!source || source.id === node.id || !placed.has(source.id)) {
          continue
        }
        pending.push({ from: source, to: node })
      }
    }
    for (const child of node.children) {
      walk(child)
    }
  }
  walk(root)

  const slots = new Map<string, number>()
  for (const item of pending) {
    slots.set(item.to.id, (slots.get(item.to.id) || 0) + 1)
  }
  const used = new Map<string, number>()
  const arrows: PrereqArrow[] = []
  for (const item of pending) {
    const from = placed.get(item.from.id)
    const to = placed.get(item.to.id)
    if (!from || !to) {
      continue
    }
    const count = slots.get(item.to.id) || 1
    const slot = used.get(item.to.id) || 0
    used.set(item.to.id, slot + 1)
    arrows.push({
      id: `${item.from.id}->${item.to.id}`,
      fromId: item.from.id,
      toId: item.to.id,
      fromTitle: item.from.title,
      toTitle: item.to.title,
      d: arrowPath(from, to, slot, count),
    })
  }
  return arrows
}
