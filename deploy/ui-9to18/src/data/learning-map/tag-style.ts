/** Tag colors + helpers for the learning map (localStorage). */

import type { LeafNote } from '@/data/learning-map/leaf-notes'
import { getMapLearnLink } from '@/data/learning-map/map-learn-links'
import type { MindNode } from '@/data/learning-map/parse-outline'

const STORAGE_KEY = 'nine-to-eighteen-map-tag-colors-v1'

/** Distinct, non-purple palette (teal / earth / sky). */
export const TAG_COLOR_PALETTE = [
  '#0d9488',
  '#ea580c',
  '#0284c7',
  '#ca8a04',
  '#16a34a',
  '#e11d48',
  '#57534e',
  '#0891b2',
  '#b45309',
  '#15803d',
  '#c2410c',
  '#0369a1',
  '#78716c',
  '#0f766e',
  '#d97706',
] as const

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function normalizeTag(tag: string): string {
  return tag.trim().toLowerCase().replace(/\s+/g, '_')
}

export function loadTagColors(): Record<string, string> {
  if (!isBrowser()) {
    return {}
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return {}
    }
    const parsed = JSON.parse(raw) as unknown
    if (!parsed || typeof parsed !== 'object') {
      return {}
    }
    const out: Record<string, string> = {}
    for (const [key, value] of Object.entries(parsed as Record<string, unknown>)) {
      const tag = normalizeTag(key)
      const color = String(value || '').trim()
      if (tag && /^#[0-9a-fA-F]{6}$/.test(color)) {
        out[tag] = color.toLowerCase()
      }
    }
    return out
  } catch {
    return {}
  }
}

export function saveTagColors(colors: Record<string, string>): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(colors))
}

export function setTagColor(
  colors: Record<string, string>,
  tag: string,
  color: string,
): Record<string, string> {
  const key = normalizeTag(tag)
  if (!key) {
    return colors
  }
  const hex = color.trim().toLowerCase()
  if (!/^#[0-9a-f]{6}$/.test(hex)) {
    return colors
  }
  return { ...colors, [key]: hex }
}

function hashTag(tag: string): number {
  let hash = 0
  for (let i = 0; i < tag.length; i += 1) {
    hash = (hash * 31 + tag.charCodeAt(i)) >>> 0
  }
  return hash
}

/** Assigned color or stable palette default. */
export function resolveTagColor(tag: string, colors: Record<string, string>): string {
  const key = normalizeTag(tag)
  if (colors[key]) {
    return colors[key]
  }
  return TAG_COLOR_PALETTE[hashTag(key) % TAG_COLOR_PALETTE.length]
}

export function getNodeTags(node: MindNode, notes: Record<string, LeafNote>): string[] {
  const note = notes[node.id]
  const raw = [...(note?.tags || []), ...(node.tags || [])]
  if (raw.length === 0) {
    const link = getMapLearnLink(node.title)
    if (link?.tags?.length) {
      raw.push(...link.tags)
    }
  }
  const seen = new Set<string>()
  const out: string[] = []
  for (const tag of raw) {
    const key = normalizeTag(tag)
    if (!key || seen.has(key)) {
      continue
    }
    seen.add(key)
    out.push(key)
  }
  return out
}

export function collectAllTags(
  root: MindNode,
  notes: Record<string, LeafNote>,
): string[] {
  const seen = new Set<string>()
  const walk = (node: MindNode): void => {
    for (const tag of getNodeTags(node, notes)) {
      seen.add(tag)
    }
    for (const child of node.children) {
      walk(child)
    }
  }
  walk(root)
  return [...seen].sort((a, b) => a.localeCompare(b, 'ru'))
}

/** Primary tag for coloring: prefer one that is in the active filter. */
export function pickPrimaryTag(
  tags: string[],
  activeTags: string[],
): string | null {
  if (tags.length === 0) {
    return null
  }
  if (activeTags.length > 0) {
    const hit = tags.find((tag) => activeTags.includes(tag))
    if (hit) {
      return hit
    }
  }
  return tags[0]
}

export function mixHex(hex: string, withHex: string, amount: number): string {
  const parse = (value: string): [number, number, number] => {
    const raw = value.replace('#', '')
    return [
      Number.parseInt(raw.slice(0, 2), 16),
      Number.parseInt(raw.slice(2, 4), 16),
      Number.parseInt(raw.slice(4, 6), 16),
    ]
  }
  const [r1, g1, b1] = parse(hex)
  const [r2, g2, b2] = parse(withHex)
  const t = Math.min(1, Math.max(0, amount))
  const to = (n: number) => n.toString(16).padStart(2, '0')
  const r = Math.round(r1 * (1 - t) + r2 * t)
  const g = Math.round(g1 * (1 - t) + g2 * t)
  const b = Math.round(b1 * (1 - t) + b2 * t)
  return `#${to(r)}${to(g)}${to(b)}`
}

export function nodeFillFromTag(tagColor: string, isRoot: boolean): string {
  return mixHex(tagColor, isRoot ? '#0f172a' : '#1e293b', isRoot ? 0.55 : 0.72)
}
