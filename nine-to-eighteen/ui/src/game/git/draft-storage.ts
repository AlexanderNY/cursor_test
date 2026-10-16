const DRAFT_KEY = 'nine-to-eighteen:git-sandbox-draft'

export function loadGitDraft(): string | null {
  if (typeof window === 'undefined' || !window.localStorage) {
    return null
  }
  try {
    const raw = window.localStorage.getItem(DRAFT_KEY)
    return raw && raw.trim() ? raw : null
  } catch {
    return null
  }
}

export function saveGitDraft(code: string): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return
  }
  try {
    window.localStorage.setItem(DRAFT_KEY, code)
  } catch {
    /* quota / private mode */
  }
}

export function clearGitDraft(): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return
  }
  try {
    window.localStorage.removeItem(DRAFT_KEY)
  } catch {
    /* ignore */
  }
}
