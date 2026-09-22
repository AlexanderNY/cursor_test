import type { MnemonicTechniqueId, StructuredMnemonicItem } from '@/data/site/structured-post'
import { isMnemonicTechniqueId } from '@/data/site/structured-post'

export type CustomMnemonicDrill = StructuredMnemonicItem & {
  id: string
  createdAt: number
  updatedAt: number
}

const STORAGE_KEY = '9to18.mnemonics.custom'

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === 'object' && !Array.isArray(value)
}

function normalizeDrill(raw: unknown): CustomMnemonicDrill | null {
  if (!isRecord(raw)) {
    return null
  }
  const technique = String(raw.technique || '').trim().toLowerCase()
  if (!isMnemonicTechniqueId(technique)) {
    return null
  }
  const items = Array.isArray(raw.items)
    ? raw.items.map((item) => String(item).trim()).filter(Boolean)
    : []
  const title = String(raw.title || '').trim() || 'Мой дрилл'
  const prompt = String(raw.prompt || '').trim()
  const hint = String(raw.hint || '').trim()
  const answer = String(raw.answer || '').trim()
  const id = String(raw.id || '').trim()
  if (!id || (!prompt && items.length === 0 && !answer)) {
    return null
  }
  return {
    id,
    technique,
    title,
    prompt,
    items,
    ...(hint ? { hint } : {}),
    ...(answer ? { answer } : {}),
    createdAt: typeof raw.createdAt === 'number' ? raw.createdAt : Date.now(),
    updatedAt: typeof raw.updatedAt === 'number' ? raw.updatedAt : Date.now(),
  }
}

export function loadCustomMnemonicDrills(
  technique?: MnemonicTechniqueId,
): CustomMnemonicDrill[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return []
    }
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) {
      return []
    }
    const drills = parsed
      .map(normalizeDrill)
      .filter((item): item is CustomMnemonicDrill => item != null)
      .sort((a, b) => b.updatedAt - a.updatedAt)
    if (!technique) {
      return drills
    }
    return drills.filter((item) => item.technique === technique)
  } catch {
    return []
  }
}

function saveAll(drills: CustomMnemonicDrill[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(drills))
  } catch {
    /* ignore quota */
  }
}

export function upsertCustomMnemonicDrill(
  input: Omit<CustomMnemonicDrill, 'id' | 'createdAt' | 'updatedAt'> & { id?: string },
): CustomMnemonicDrill {
  const all = loadCustomMnemonicDrills()
  const now = Date.now()
  const existingIndex = input.id ? all.findIndex((item) => item.id === input.id) : -1
  if (existingIndex >= 0) {
    const prev = all[existingIndex]
    const next: CustomMnemonicDrill = {
      ...prev,
      ...input,
      id: prev.id,
      createdAt: prev.createdAt,
      updatedAt: now,
      items: input.items.map((item) => item.trim()).filter(Boolean),
      title: input.title.trim() || 'Мой дрилл',
      prompt: input.prompt.trim(),
      hint: input.hint?.trim() || undefined,
      answer: input.answer?.trim() || undefined,
    }
    all[existingIndex] = next
    saveAll(all)
    return next
  }
  const created: CustomMnemonicDrill = {
    id: `custom-${now}-${Math.random().toString(36).slice(2, 8)}`,
    technique: input.technique,
    title: input.title.trim() || 'Мой дрилл',
    prompt: input.prompt.trim(),
    items: input.items.map((item) => item.trim()).filter(Boolean),
    hint: input.hint?.trim() || undefined,
    answer: input.answer?.trim() || undefined,
    createdAt: now,
    updatedAt: now,
  }
  saveAll([created, ...all])
  return created
}

export function deleteCustomMnemonicDrill(id: string): void {
  saveAll(loadCustomMnemonicDrills().filter((item) => item.id !== id))
}
