import gameConfig from '../../../public/bowl/game-config.json'

export type GameConfig = typeof gameConfig

export const GAME_CONFIG: GameConfig = gameConfig

let autosaveIntervalMs = gameConfig.autosave_interval_ms

export function getAutosaveIntervalMs(): number {
  return autosaveIntervalMs
}

export function setAutosaveIntervalMs(value: number): void {
  autosaveIntervalMs = value
}
