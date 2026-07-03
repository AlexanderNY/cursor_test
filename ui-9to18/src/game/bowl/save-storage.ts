import { SAVE_KEY } from './types'

export function hasSave(): boolean {
  try {
    return localStorage.getItem(SAVE_KEY) !== null
  } catch {
    return false
  }
}

export function loadSave(): string | null {
  try {
    return localStorage.getItem(SAVE_KEY)
  } catch {
    return null
  }
}

export function writeSave(stateJson: string): void {
  try {
    localStorage.setItem(SAVE_KEY, stateJson)
  } catch {
    // ignore quota / privacy mode
  }
}

export function clearSave(): void {
  try {
    localStorage.removeItem(SAVE_KEY)
  } catch {
    // ignore
  }
}
