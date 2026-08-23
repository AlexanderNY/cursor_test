import { DEFAULT_HERO_COLOR } from './hero-colors'
import { defaultPerkLevels, maxAllPerks, PERK_IDS, type PerkId, type PerkLevels } from './perks'

const STORAGE_KEY = 'bowl-character-editor-v1'

export interface CharacterEditorDraft {
  color: string
  perkLevels: PerkLevels
}

export { maxAllPerks }

export function loadCharacterEditorDraft(): CharacterEditorDraft {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return { color: DEFAULT_HERO_COLOR, perkLevels: defaultPerkLevels() }
    }
    const parsed = JSON.parse(raw) as Partial<CharacterEditorDraft>
    const perkLevels = defaultPerkLevels()
    for (const id of PERK_IDS) {
      const level = Number(parsed.perkLevels?.[id] ?? 0)
      perkLevels[id] = Math.max(0, Math.min(level, 3))
    }
    return {
      color: typeof parsed.color === 'string' ? parsed.color : DEFAULT_HERO_COLOR,
      perkLevels,
    }
  } catch {
    return { color: DEFAULT_HERO_COLOR, perkLevels: defaultPerkLevels() }
  }
}

export function saveCharacterEditorDraft(draft: CharacterEditorDraft): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(draft))
}

export function setPerkLevel(
  perkLevels: PerkLevels,
  perkId: PerkId,
  level: number,
  maxLevel: number,
): PerkLevels {
  return {
    ...defaultPerkLevels(),
    ...perkLevels,
    [perkId]: Math.max(0, Math.min(level, maxLevel)),
  }
}
