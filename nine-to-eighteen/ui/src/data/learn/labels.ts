/** Learn article taxonomy labels (track / level). */

export const LEARN_PROFILES = [
  { id: 'analyst', label: 'Аналитик' },
  { id: 'devops', label: 'DevOps' },
  { id: 'developer', label: 'Разработчик' },
  { id: 'tester', label: 'Тестировщик' },
  { id: 'product_owner', label: 'Владелец продукта' },
] as const

export type LearnProfileId = (typeof LEARN_PROFILES)[number]['id']

export const LEARN_LEVELS = [
  { id: 'intern', label: 'Intern' },
  { id: 'junior', label: 'Junior' },
  { id: 'middle', label: 'Middle' },
  { id: 'senior', label: 'Senior' },
  { id: 'lead', label: 'Lead' },
] as const

export type LearnLevelId = (typeof LEARN_LEVELS)[number]['id']

const PROFILE_IDS = new Set<string>(LEARN_PROFILES.map((p) => p.id))
const LEVEL_IDS = new Set<string>(LEARN_LEVELS.map((l) => l.id))

export function isLearnProfileId(value: string): value is LearnProfileId {
  return PROFILE_IDS.has(value)
}

export function isLearnLevelId(value: string): value is LearnLevelId {
  return LEVEL_IDS.has(value)
}

export function profileLabel(id: string): string {
  return LEARN_PROFILES.find((p) => p.id === id)?.label || id
}

export function levelLabel(id: string): string {
  return LEARN_LEVELS.find((l) => l.id === id)?.label || id
}

export function normalizeProfiles(raw: unknown): LearnProfileId[] {
  if (!Array.isArray(raw)) {
    return []
  }
  const out: LearnProfileId[] = []
  const seen = new Set<string>()
  for (const item of raw) {
    const id = String(item || '')
      .trim()
      .toLowerCase()
    if (!isLearnProfileId(id) || seen.has(id)) {
      continue
    }
    seen.add(id)
    out.push(id)
  }
  return out
}

export function normalizeLevel(raw: unknown): LearnLevelId | '' {
  const id = String(raw || '')
    .trim()
    .toLowerCase()
  return isLearnLevelId(id) ? id : ''
}

export function normalizeStringList(raw: unknown, maxItemLen = 64, maxItems = 32): string[] {
  if (!Array.isArray(raw)) {
    if (typeof raw === 'string' && raw.trim()) {
      return raw
        .split(/[,;]/)
        .map((s) => s.trim().slice(0, maxItemLen))
        .filter(Boolean)
        .slice(0, maxItems)
    }
    return []
  }
  const out: string[] = []
  const seen = new Set<string>()
  for (const item of raw) {
    const value = String(item || '')
      .trim()
      .slice(0, maxItemLen)
    if (!value) {
      continue
    }
    const key = value.toLowerCase()
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    out.push(value)
    if (out.length >= maxItems) {
      break
    }
  }
  return out
}

/** Tag + badge for articles linked from the interview / knowledge map. */
export const LEARN_KNOWLEDGE_MAP_TAG = 'собеседование'

export function hasKnowledgeMapTag(tags: string[] | undefined | null): boolean {
  const needle = LEARN_KNOWLEDGE_MAP_TAG.toLowerCase()
  return (tags || []).some((tag) => tag.trim().toLowerCase() === needle)
}

/** Add or remove the «собеседование» tag used for the knowledge map. */
export function withKnowledgeMapTag(tags: string[], enabled: boolean): string[] {
  const without = normalizeStringList(tags).filter(
    (tag) => tag.toLowerCase() !== LEARN_KNOWLEDGE_MAP_TAG.toLowerCase(),
  )
  if (!enabled) {
    return without
  }
  return [...without, LEARN_KNOWLEDGE_MAP_TAG]
}
