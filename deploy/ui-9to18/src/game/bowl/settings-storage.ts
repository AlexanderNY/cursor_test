import { GAME_CONFIG, type GameConfig } from './game-config'
import { EDITABLE_SETTINGS } from './settings-schema'

export const SETTINGS_OVERRIDES_KEY = 'bowl-settings-overrides-v1'

const EDITABLE_KEYS = new Set(EDITABLE_SETTINGS.map((field) => field.key))

export function loadSettingsOverrides(): Partial<GameConfig> {
  try {
    const raw = localStorage.getItem(SETTINGS_OVERRIDES_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw) as Partial<GameConfig>
    const filtered: Partial<GameConfig> = {}
    for (const key of EDITABLE_KEYS) {
      if (key in parsed) {
        filtered[key] = parsed[key] as never
      }
    }
    return filtered
  } catch {
    return {}
  }
}

export function saveSettingsOverrides(overrides: Partial<GameConfig>): void {
  localStorage.setItem(SETTINGS_OVERRIDES_KEY, JSON.stringify(overrides))
}

export function clearSettingsOverrides(): void {
  localStorage.removeItem(SETTINGS_OVERRIDES_KEY)
}

export function mergeGameConfig(
  base: GameConfig = GAME_CONFIG,
  overrides: Partial<GameConfig> = loadSettingsOverrides(),
): GameConfig {
  return { ...base, ...overrides }
}

export async function fetchBaseGameConfig(): Promise<GameConfig> {
  const response = await fetch('/bowl/game-config.json')
  if (!response.ok) {
    throw new Error(`Failed to load game-config.json: ${response.status}`)
  }
  return response.json() as Promise<GameConfig>
}

export async function loadEffectiveGameConfig(): Promise<GameConfig> {
  const base = await fetchBaseGameConfig()
  return mergeGameConfig(base, loadSettingsOverrides())
}
