export const SAVE_KEY = 'bowl-save-v1'

export const PY_FILES = [
  'config.py',
  'entities.py',
  'perks.py',
  'physics.py',
  'combat.py',
  'spawn_system.py',
  'save_codec.py',
  'game_engine.py',
] as const

export const PY_AI_FILES = ['ai/__init__.py', 'ai/mob_brain.py'] as const

export const PY_BASE_PATH = '/bowl/py'
export const PY_VFS_PATH = '/bowl/py'
export const GAME_CONFIG_PATH = '/bowl/game-config.json'
export const PERKS_CONFIG_PATH = '/bowl/perks.json'

export type GamePhase = 'normal' | 'whirlpool' | 'boss'

export type GameScreen = 'loading' | 'menu' | 'settings' | 'colorSelect' | 'perkSelect' | 'playing' | 'gameOver'

export type PickupKind = 'green' | 'red'
export type EnemyState = 'patrol' | 'chase' | 'cooldown' | 'flee'
export type PerkKind = 'leg' | 'eye' | 'tentacle' | 'spike'
export type ObstacleKind = 'paper' | 'toothbrush'

export interface RenderState {
  level: number
  eat_count: number
  enemies_eaten: number
  enemies_eaten_mod: number
  enemies_per_perk: number
  pending_perk_select: boolean
  world: { width: number; height: number }
  bowl: { cx: number; cy: number; rx: number; ry: number }
  camera: { x: number; y: number }
  visibility_radius: number
  lightness_mult: number
  player: {
    x: number
    y: number
    radius: number
    red: number
    green: number
    weight: number
    perk_levels: Record<string, number>
    perks: PerkKind[]
    facing_angle: number
    color: string
  }
  obstacles: Array<{
    x: number
    y: number
    kind: ObstacleKind
    radius: number
    angle: number
    width: number
    height: number
  }>
  pickups: Array<{
    x: number
    y: number
    radius: number
    kind: PickupKind
    spike_angle: number
    attached_to: number | null
  }>
  enemies: Array<{
    x: number
    y: number
    radius: number
    health: number
    max_health: number
    state: EnemyState
    is_boss?: boolean
  }>
  game_over: boolean
  phase: GamePhase
  match_timer: number
  match_timer_total: number
  whirlpool_time_left: number
  whirlpool_duration: number
  whirlpool_angle: number
  whirlpool_radius: number
  boss_active: boolean
}

export interface InputVector {
  x: number
  y: number
}

export type ProgressCallback = (progress: number, label: string) => void
