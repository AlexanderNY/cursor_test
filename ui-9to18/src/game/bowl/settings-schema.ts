import type { GameConfig } from './game-config'

export type SettingKind = 'number' | 'boolean'

export interface SettingField {
  key: keyof GameConfig
  label: string
  group: string
  kind: SettingKind
  min?: number
  max?: number
  step?: number
  hint?: string
  newGameOnly?: boolean
}

export const SETTING_GROUPS = [
  'Игрок',
  'Видимость и бой',
  'Спавн на краях',
  'События матча',
  'Физика',
] as const

export const EDITABLE_SETTINGS: SettingField[] = [
  {
    key: 'player_speed',
    label: 'Макс. скорость игрока',
    group: 'Игрок',
    kind: 'number',
    min: 200,
    max: 5000,
    step: 50,
  },
  {
    key: 'physics_player_accel',
    label: 'Ускорение игрока',
    group: 'Игрок',
    kind: 'number',
    min: 500,
    max: 20000,
    step: 100,
  },
  {
    key: 'base_player_radius',
    label: 'Стартовый радиус',
    group: 'Игрок',
    kind: 'number',
    min: 10,
    max: 40,
    step: 1,
    newGameOnly: true,
  },
  {
    key: 'base_visibility_radius',
    label: 'Радиус видимости',
    group: 'Видимость и бой',
    kind: 'number',
    min: 60,
    max: 280,
    step: 10,
  },
  {
    key: 'enemies_per_perk',
    label: 'Врагов на перк',
    group: 'Видимость и бой',
    kind: 'number',
    min: 3,
    max: 30,
    step: 1,
  },
  {
    key: 'hit_damage',
    label: 'Урон от врага',
    group: 'Видимость и бой',
    kind: 'number',
    min: 5,
    max: 50,
    step: 1,
  },
  {
    key: 'enemy_count',
    label: 'Врагов при старте',
    group: 'Видимость и бой',
    kind: 'number',
    min: 0,
    max: 40,
    step: 1,
    newGameOnly: true,
  },
  {
    key: 'green_pickup_count',
    label: 'Зелёных точек при старте',
    group: 'Видимость и бой',
    kind: 'number',
    min: 0,
    max: 120,
    step: 5,
    newGameOnly: true,
  },
  {
    key: 'edge_spawn_enabled',
    label: 'Спавн на краях карты',
    group: 'Спавн на краях',
    kind: 'boolean',
  },
  {
    key: 'edge_spawn_green_interval_sec',
    label: 'Интервал зелёных (сек)',
    group: 'Спавн на краях',
    kind: 'number',
    min: 2,
    max: 60,
    step: 1,
  },
  {
    key: 'edge_spawn_red_interval_sec',
    label: 'Интервал красных (сек)',
    group: 'Спавн на краях',
    kind: 'number',
    min: 2,
    max: 60,
    step: 1,
  },
  {
    key: 'edge_spawn_enemy_interval_sec',
    label: 'Интервал мобов (сек)',
    group: 'Спавн на краях',
    kind: 'number',
    min: 3,
    max: 90,
    step: 1,
  },
  {
    key: 'max_enemies',
    label: 'Макс. врагов на карте',
    group: 'Спавн на краях',
    kind: 'number',
    min: 3,
    max: 50,
    step: 1,
  },
  {
    key: 'match_timer_sec',
    label: 'До водоворота (сек)',
    group: 'События матча',
    kind: 'number',
    min: 30,
    max: 600,
    step: 10,
  },
  {
    key: 'whirlpool_duration_sec',
    label: 'Длительность водоворота (сек)',
    group: 'События матча',
    kind: 'number',
    min: 3,
    max: 60,
    step: 1,
  },
  {
    key: 'boss_speed',
    label: 'Скорость босса',
    group: 'События матча',
    kind: 'number',
    min: 80,
    max: 400,
    step: 10,
  },
  {
    key: 'physics_friction',
    label: 'Трение',
    group: 'Физика',
    kind: 'number',
    min: 1,
    max: 12,
    step: 0.5,
  },
  {
    key: 'push_strength',
    label: 'Сила толкания',
    group: 'Физика',
    kind: 'number',
    min: 40,
    max: 400,
    step: 10,
  },
  {
    key: 'physics_max_speed',
    label: 'Макс. скорость объектов',
    group: 'Физика',
    kind: 'number',
    min: 120,
    max: 1500,
    step: 20,
  },
]

export function groupSettings(fields: SettingField[]): Map<string, SettingField[]> {
  const map = new Map<string, SettingField[]>()
  for (const field of fields) {
    const list = map.get(field.group) ?? []
    list.push(field)
    map.set(field.group, list)
  }
  return map
}
