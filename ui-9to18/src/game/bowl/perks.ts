import perksData from '../../../public/bowl/perks.json'

export type PerkId = keyof typeof perksData

export type PerkLevelStats = Record<string, number | string>

export interface PerkDefinition {
  id: string
  title: string
  emoji: string
  max_level: number
  levels: Record<string, PerkLevelStats & { description: string }>
}

export const PERK_DEFINITIONS = perksData as Record<PerkId, PerkDefinition>

export const PERK_IDS = Object.keys(PERK_DEFINITIONS) as PerkId[]

export type PerkLevels = Partial<Record<PerkId, number>>

export function getPerkLevel(perkLevels: PerkLevels, perkId: PerkId): number {
  return perkLevels[perkId] ?? 0
}

export function canUpgradePerk(perkLevels: PerkLevels, perkId: PerkId): boolean {
  const def = PERK_DEFINITIONS[perkId]
  if (!def) return false
  return getPerkLevel(perkLevels, perkId) < def.max_level
}

export function getUpgradeOptions(perkLevels: PerkLevels): Array<{
  id: PerkId
  nextLevel: number
  title: string
  emoji: string
  description: string
}> {
  return PERK_IDS.filter((id) => canUpgradePerk(perkLevels, id)).map((id) => {
    const def = PERK_DEFINITIONS[id]
    const nextLevel = getPerkLevel(perkLevels, id) + 1
    const stats = def.levels[String(nextLevel)]
    return {
      id,
      nextLevel,
      title: `${def.title} · ур. ${nextLevel}`,
      emoji: def.emoji,
      description: stats?.description ?? def.title,
    }
  })
}

export function formatPerkLevels(perkLevels: PerkLevels): string {
  const parts = PERK_IDS.filter((id) => getPerkLevel(perkLevels, id) > 0).map(
    (id) => `${PERK_DEFINITIONS[id].title} ${getPerkLevel(perkLevels, id)}`,
  )
  return parts.length > 0 ? parts.join(', ') : '—'
}

export function perkLevelsFromLegacy(perks: string[]): PerkLevels {
  const levels: PerkLevels = {}
  for (const id of perks) {
    if (id in PERK_DEFINITIONS) {
      levels[id as PerkId] = 1
    }
  }
  return levels
}
