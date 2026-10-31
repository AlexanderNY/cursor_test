/** Запомненный вид карты: раскрытие, масштаб и панорама по профилю. */

export type MapViewState = {
  expandedIds: string[]
  zoom: number
  pan: { x: number; y: number }
}

const STORAGE_KEY = 'nine-to-eighteen-map-view-v2'

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function mapViewKey(profileId: string | null): string {
  return profileId || 'all'
}

function readAll(): Record<string, MapViewState> {
  if (!isBrowser()) {
    return {}
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return {}
    }
    const parsed = JSON.parse(raw) as unknown
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      return {}
    }
    return parsed as Record<string, MapViewState>
  } catch {
    return {}
  }
}

function parseView(value: unknown): MapViewState | null {
  if (!value || typeof value !== 'object') {
    return null
  }
  const row = value as Partial<MapViewState>
  const zoom = Number(row.zoom)
  const panX = Number(row.pan?.x)
  const panY = Number(row.pan?.y)
  if (!Number.isFinite(zoom) || !Number.isFinite(panX) || !Number.isFinite(panY)) {
    return null
  }
  const expandedIds = Array.isArray(row.expandedIds)
    ? row.expandedIds.map((id) => String(id)).filter(Boolean)
    : []
  return {
    expandedIds,
    zoom,
    pan: { x: panX, y: panY },
  }
}

export function loadMapView(profileId: string | null): MapViewState | null {
  const stored = readAll()[mapViewKey(profileId)]
  return parseView(stored)
}

export function saveMapView(profileId: string | null, view: MapViewState): void {
  if (!isBrowser()) {
    return
  }
  const all = readAll()
  all[mapViewKey(profileId)] = {
    expandedIds: [...new Set(view.expandedIds)],
    zoom: view.zoom,
    pan: { x: view.pan.x, y: view.pan.y },
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(all))
}
