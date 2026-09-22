/** Persist which L1 learning-map branches are hidden (client-only). */

const STORAGE_KEY = 'nine-to-eighteen-map-hidden-branches-v1'

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function loadHiddenBranchIds(): string[] {
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
    return parsed.map((id) => String(id)).filter(Boolean)
  } catch {
    return []
  }
}

export function saveHiddenBranchIds(ids: string[]): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify([...new Set(ids)]))
}
