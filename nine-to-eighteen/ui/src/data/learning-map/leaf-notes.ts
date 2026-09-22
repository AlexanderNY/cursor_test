/** Per-leaf notes (description + tags) for the learning map, stored in the browser. */

export type LeafNote = {
  description: string
  tags: string[]
}

const STORAGE_KEY = 'nine-to-eighteen-map-leaf-notes-v1'

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

export function loadLeafNotes(): Record<string, LeafNote> {
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
    const out: Record<string, LeafNote> = {}
    for (const [id, value] of Object.entries(parsed as Record<string, unknown>)) {
      if (!value || typeof value !== 'object') {
        continue
      }
      const row = value as Partial<LeafNote>
      out[id] = {
        description: String(row.description || ''),
        tags: Array.isArray(row.tags)
          ? row.tags.map((tag) => String(tag).trim()).filter(Boolean)
          : [],
      }
    }
    return out
  } catch {
    return {}
  }
}

export function saveLeafNotes(notes: Record<string, LeafNote>): void {
  if (!isBrowser()) {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(notes))
}

export function upsertLeafNote(
  notes: Record<string, LeafNote>,
  nodeId: string,
  patch: Partial<LeafNote>,
): Record<string, LeafNote> {
  const prev = notes[nodeId] || { description: '', tags: [] }
  const next: LeafNote = {
    description: patch.description != null ? patch.description : prev.description,
    tags: patch.tags != null ? patch.tags : prev.tags,
  }
  if (!next.description.trim() && next.tags.length === 0) {
    const { [nodeId]: _removed, ...rest } = notes
    return rest
  }
  return { ...notes, [nodeId]: next }
}
