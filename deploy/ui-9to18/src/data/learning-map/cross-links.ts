/** Cross-branch dashed links between leaf nodes on the learning map. */

export type MapCrossLink = {
  /** Stable node ids from outline parse (`n12`, …), unordered pair stored sorted. */
  a: string
  b: string
}

const STORAGE_KEY = 'nine-to-eighteen-map-cross-links-v1'

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function normalizePair(a: string, b: string): MapCrossLink | null {
  const left = a.trim()
  const right = b.trim()
  if (!left || !right || left === right) {
    return null
  }
  return left < right ? { a: left, b: right } : { a: right, b: left }
}

export function loadCrossLinks(): MapCrossLink[] {
  if (!isBrowser()) {
    return []
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) {
      return []
    }
    const out: MapCrossLink[] = []
    const seen = new Set<string>()
    for (const item of parsed) {
      if (!item || typeof item !== 'object') {
        continue
      }
      const pair = normalizePair(
        String((item as MapCrossLink).a || ''),
        String((item as MapCrossLink).b || ''),
      )
      if (!pair) {
        continue
      }
      const key = `${pair.a}|${pair.b}`
      if (seen.has(key)) {
        continue
      }
      seen.add(key)
      out.push(pair)
    }
    return out
  } catch {
    return []
  }
}

export function saveCrossLinks(links: MapCrossLink[]): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(links))
}

export function addCrossLink(links: MapCrossLink[], a: string, b: string): MapCrossLink[] {
  const pair = normalizePair(a, b)
  if (!pair) {
    return links
  }
  if (links.some((link) => link.a === pair.a && link.b === pair.b)) {
    return links
  }
  return [...links, pair]
}

export function removeCrossLink(links: MapCrossLink[], a: string, b: string): MapCrossLink[] {
  const pair = normalizePair(a, b)
  if (!pair) {
    return links
  }
  return links.filter((link) => !(link.a === pair.a && link.b === pair.b))
}

export function crossLinkPath(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
): string {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const len = Math.hypot(dx, dy) || 1
  // Offset control point perpendicular to the chord for a soft arc
  const ox = (-dy / len) * Math.min(80, len * 0.22)
  const oy = (dx / len) * Math.min(80, len * 0.22)
  return `M ${x1} ${y1} Q ${mx + ox} ${my + oy} ${x2} ${y2}`
}
