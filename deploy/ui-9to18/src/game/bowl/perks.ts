import perksData from '../../../public/bowl/perks.json'

export type PerkId = keyof typeof perksData

export type PerkLevelStats = Record<string, number | string | boolean>

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

export function defaultPerkLevels(): PerkLevels {
  const levels: PerkLevels = {}
  for (const id of PERK_IDS) {
    levels[id] = 0
  }
  return levels
}

export function getPerkLevel(perkLevels: PerkLevels, perkId: PerkId): number {
  return perkLevels[perkId] ?? 0
}

export function getPerkStats(perkLevels: PerkLevels, perkId: PerkId) {
  const level = getPerkLevel(perkLevels, perkId)
  return PERK_DEFINITIONS[perkId].levels[String(level)] ?? PERK_DEFINITIONS[perkId].levels['0']
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

export function getPerkLimbCount(perkLevels: PerkLevels, perkId: PerkId): number {
  const stats = getPerkStats(perkLevels, perkId)
  return Number(stats?.limb_count ?? 0)
}

export function isPerkStub(perkLevels: PerkLevels, perkId: PerkId): boolean {
  return Boolean(getPerkStats(perkLevels, perkId)?.stub)
}

export function isPerkDotsOnly(perkLevels: PerkLevels, perkId: PerkId): boolean {
  return Boolean(getPerkStats(perkLevels, perkId)?.dots_only)
}

export function isPerkWaves(perkLevels: PerkLevels, perkId: PerkId): boolean {
  return Boolean(getPerkStats(perkLevels, perkId)?.waves)
}

export function getSpikeDrawStats(perkLevels: PerkLevels): {
  count: number
  length: number
  damage: number
  forehead: boolean
} {
  const stats = getPerkStats(perkLevels, 'spike')
  return {
    count: Number(stats?.spike_count ?? 0),
    length: Number(stats?.spike_length ?? 0),
    damage: Number(stats?.damage ?? 0),
    forehead: Boolean(stats?.forehead),
  }
}

export function formatPerkLevels(perkLevels: PerkLevels): string {
  const parts = PERK_IDS.map(
    (id) => `${PERK_DEFINITIONS[id].title} ${getPerkLevel(perkLevels, id)}`,
  )
  return parts.join(', ')
}

export function perkLevelsFromLegacy(perks: string[]): PerkLevels {
  const levels = defaultPerkLevels()
  for (const id of perks) {
    if (id in PERK_DEFINITIONS) {
      levels[id as PerkId] = Math.max(levels[id as PerkId] ?? 0, 1)
    }
  }
  return levels
}

export function maxAllPerks(): PerkLevels {
  const levels: PerkLevels = defaultPerkLevels()
  for (const id of PERK_IDS) {
    levels[id] = 3
  }
  return levels
}
