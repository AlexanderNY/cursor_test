const HIGH_SCORE_KEY = 'bowl-high-score-v1'

export function loadHighScore(): number {
  try {
    const raw = localStorage.getItem(HIGH_SCORE_KEY)
    const value = Number(raw)
    return Number.isFinite(value) && value > 0 ? Math.floor(value) : 0
  } catch {
    return 0
  }
}

export function saveHighScore(score: number): number {
  const next = Math.max(0, Math.floor(score))
  const best = Math.max(loadHighScore(), next)
  try {
    localStorage.setItem(HIGH_SCORE_KEY, String(best))
  } catch {
    // ignore quota / private mode
  }
  return best
}
